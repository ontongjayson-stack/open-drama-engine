import json
from unittest.mock import Mock
import pytest
from PIL import Image
from prompt_guard import PromptGuard, ContinuityError
from project_continuity import ProjectContinuity, frame, pixel_hash, creator_export
from story_media import render_scene, run_media
from assemble_clips import build_master_story


def test_typed_review_rejects_uncertainty_and_malformed_answers(monkeypatch, tmp_path):
    monkeypatch.delenv('TYPESAFE_API_KEY', raising=False)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'existing-writer-test')
    answer = {'passed': True, 'uncertain': False, 'evidence': ['Both state fields specify silver hair.']}
    request = Mock()
    monkeypatch.setattr('story_writer.StoryWriter.request', request)
    for bad in (dict(answer, uncertain=True), dict(answer, passed='true'), dict(answer, evidence=[])):
        request.return_value = {'answers': {'identity': bad}}
        with pytest.raises(ContinuityError):
            PromptGuard().approve({}, {'identity': 'Same character?'})
    request.return_value = {'answers': {'identity': answer}}
    audit = tmp_path / 'audit.json'
    assert PromptGuard().approve({}, {'identity': 'Same character?'}, audit)['accepted']
    assert 'existing-writer-test' not in audit.read_text()
    assert 'probabilities' not in audit.read_text()


def test_missing_typesafe_key_does_not_block_api(monkeypatch, tmp_path):
    import app
    from fastapi.testclient import TestClient
    monkeypatch.delenv('TYPESAFE_API_KEY', raising=False)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'existing-writer-test')
    monkeypatch.setattr(app, 'ASSETS_DIR', tmp_path)
    monkeypatch.setattr(app.router, '_refresh_keys', lambda: None)
    monkeypatch.setattr(app.router, 'keys', {'gemini':'existing-vision-test'})
    monkeypatch.setattr(app, 'run_orchestration_job', lambda *args: app.production_lock.release())
    response = TestClient(app.app).post('/api/generate', json={'prompt': 'A guardian rescues a village'})
    assert response.status_code == 200
    assert response.json()['status'] == 'started'


def test_real_lossless_frame_handoff_and_master_join(tmp_path):
    first, second = tmp_path / 'first.png', tmp_path / 'second.png'
    pattern = Image.new('RGB', (768,432))
    pattern.putdata([((x*7+y*3)%256, (x+y*5)%256, (x*11+y)%256) for y in range(432) for x in range(768)])
    pattern.save(first)
    Image.new('RGB', (768,432), (181,120,45)).save(second)
    a,b = tmp_path / 'a.mp4', tmp_path / 'b.mp4'
    render_scene(first, None, 1, a, strict_continuity=True)
    end = frame(a, tmp_path / 'end.png', last=True)
    render_scene(second, None, 1, b, strict_continuity=True, continuity_start=end)
    assert pixel_hash(frame(b, tmp_path / 'start.png')) == pixel_hash(end)
    continuity = ProjectContinuity(tmp_path, {'title':'Test','character_bible':'Mira','shots':[]}, {})
    continuity.approve_clip(b, 2, end)
    with pytest.raises(ContinuityError, match='exact decoded'):
        continuity.approve_clip(a, 3, second)
    master = build_master_story(tmp_path, clips=[a,b], expected_duration=2)
    for n in (23,24):
        run_media(['ffmpeg','-y','-v','error','-i',master,'-vf',f'select=eq(n\\,{n})','-frames:v','1',str(tmp_path / f'join{n}.png')])
    assert pixel_hash(tmp_path / 'join23.png') == pixel_hash(tmp_path / 'join24.png')
    creator_export(master, [a,b], tmp_path)
    from story_media import probe
    video = next(s for s in probe(master)['streams'] if s['codec_type'] == 'video')
    assert video['pix_fmt'] == 'yuv420p'
    assert abs(float(probe(master)['format']['duration']) - 2) < .03


def test_canon_and_reference_cannot_change(tmp_path):
    story = {'title':'Test','character_bible':'Mira silver hair','shots':[]}
    continuity = ProjectContinuity(tmp_path, story, {})
    reference = tmp_path / 'character_reference.png'
    Image.new('RGB', (8,8), 'red').save(reference)
    continuity.lock_reference(reference)
    ProjectContinuity(tmp_path, story, {})
    with pytest.raises(ContinuityError, match='canon differs'):
        ProjectContinuity(tmp_path, dict(story,character_bible='Mira blue hair'), {})
    Image.new('RGB', (8,8), 'blue').save(reference)
    with pytest.raises(ContinuityError, match='reference has changed'):
        ProjectContinuity(tmp_path, story, {})


def test_uncertain_visual_observation_is_rejected(tmp_path, monkeypatch):
    continuity = ProjectContinuity(tmp_path, {'title':'Test','character_bible':'Mira silver hair','shots':[]}, {'gemini':'unit-test'})
    image = tmp_path / 'art.png'
    Image.new('RGB',(16,16),'red').save(image)
    response = Mock(ok=True)
    response.json.return_value = {'candidates':[{'content':{'parts':[{'text': json.dumps({'observations':'Face is obscured','contradictions':[],'uncertain':True})}]}}]}
    monkeypatch.setattr('project_continuity.requests.post', lambda *a,**k:response)
    with pytest.raises(ContinuityError,match='uncertain'):
        continuity.observe([('scene',image)], 'Compare identity')


def test_vision_service_failure_uses_existing_openrouter(tmp_path, monkeypatch):
    monkeypatch.setenv("ALLOW_OPENROUTER_VISION", "1")
    continuity = ProjectContinuity(tmp_path, {'title':'Test','character_bible':'Mira','shots':[]}, {'gemini':'vision-test','openrouter':'writer-test'})
    image = tmp_path / 'art.png'
    Image.new('RGB',(16,16),'red').save(image)
    unavailable = Mock(ok=False,status_code=503)
    fallback = Mock(ok=True)
    fallback.json.return_value = {'choices':[{'message':{'content':json.dumps({'observations':'Mira has canonical silver hair.','contradictions':[],'uncertain':False})}}]}
    post = Mock(side_effect=[unavailable,fallback])
    monkeypatch.setattr('project_continuity.requests.post',post)
    assert continuity.observe([('scene',image)],'Compare identity')['uncertain'] is False
    assert post.call_args_list[1].kwargs['json']['messages'][0]['content'][-1]['type'] == 'image_url'


def test_writer_rejects_discontinuous_scene_states(monkeypatch):
    from story_writer import StoryWriter
    monkeypatch.setattr('story_writer.PromptGuard',lambda:Mock())
    writer = StoryWriter({})
    bad_batch = {'shots':[{'prompt':'Mira at river','narration':'Mira followed the river.','start_state':'river','end_state':'river'}, {'prompt':'Mira at home','narration':'Mira suddenly arrived home.','start_state':'home','end_state':'home'}]}
    writer.request = Mock(side_effect=[{'title':'Guardian','character_bible':'Mira','acts':['act']*6},bad_batch,bad_batch])
    with pytest.raises(ContinuityError,match='previous ending'):
        writer.write('Guardian story','Anime',24)


def test_vision_fallback_does_not_send_images_without_authorization(tmp_path,monkeypatch):
    monkeypatch.delenv('ALLOW_OPENROUTER_VISION',raising=False)
    continuity=ProjectContinuity(tmp_path,{'title':'Test','character_bible':'Mira','shots':[]},{'openrouter':'writer-test'})
    image=tmp_path/'art.png'
    Image.new('RGB',(16,16),'red').save(image)
    post=Mock()
    monkeypatch.setattr('project_continuity.requests.post',post)
    with pytest.raises(ContinuityError,match='explicit approval'):
        continuity.observe([('scene',image)],'Compare identity')
    post.assert_not_called()
