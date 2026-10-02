"""Regression checks for real media timing, job isolation, and failed providers."""
import asyncio
import json
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app as studio
from assemble_clips import build_master_story, get_video_duration, is_valid_mp4
from comfy_client import ComfyClient
from story_media import captions, render_scene, probe
from story_writer import StoryWriter
from render_engine import RenderEngine


@pytest.fixture(autouse=True)
def writer_judgment_double(monkeypatch):
    monkeypatch.setattr("story_writer.PromptGuard", lambda: Mock())


@pytest.fixture
def client():
    return TestClient(studio.app)


@pytest.mark.parametrize("payload", [{"duration": 0}, {"duration": 1501}, {"aspect_ratio": "4:3"}, {"prompt": "    "}, {"production_mode": "unknown"}])
def test_invalid_requests_are_rejected(client, payload):
    response = client.post('/api/generate', json=dict({"prompt": "A guardian rescues a village"}, **payload))
    assert response.status_code == 422


def test_long_motion_is_rejected(client):
    assert client.post('/api/generate', json={"prompt": "A guardian rescues a village", "duration": 300, "production_mode": "motion"}).status_code == 422


def test_concurrent_job_is_rejected(client):
    assert studio.production_lock.acquire(False)
    try:
        assert client.post('/api/generate', json={"prompt": "A guardian rescues a village"}).status_code == 409
    finally:
        studio.production_lock.release()


def test_long_request_and_script_budget():
    request = studio.ProductionRequest(prompt="A guardian rescues a village", duration=1500)
    assert request.duration == 1500
    writer = StoryWriter({})
    writer.request = Mock(side_effect=[{"title": "Guardian", "character_bible": "Mira, silver hair and blue cloak", "acts": [str(i) for i in range(6)]}, {"shots": [{"start_state": "river", "end_state": "river", "prompt": "Mira crosses the valley", "narration": "Mira followed the river to save her home."} for _ in range(6)]}, {"shots": [{"start_state": "river", "end_state": "river", "prompt": "Mira returns home", "narration": "The village welcomed Mira home after the storm."} for _ in range(4)]}])
    story = writer.write("Guardian saves village", "Anime", 120)
    assert len(story['shots']) == 10
    assert sum(s['duration'] for s in story['shots']) == 120
    assert story['shots'][-1]['id'] == 10


def test_failed_writer_never_exports_placeholder():
    with pytest.raises(RuntimeError, match="API key missing"):
        StoryWriter({}).write('A guardian rescues a village', 'Anime', 300)


def test_writer_recovers_from_exhausted_reasoning_budget(monkeypatch):
    first = Mock()
    first.json.return_value = {'choices': [{'finish_reason': 'length', 'message': {'content': None}}]}
    second = Mock()
    second.json.return_value = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{"title":"Guardian"}'}}]}
    post = Mock(side_effect=[first, second])
    monkeypatch.setattr('story_writer.requests.post', post)
    monkeypatch.delenv('OPENROUTER_MODEL', raising=False)
    result = StoryWriter({'openrouter': 'test-key'}).request('Return a title')
    assert result['title'] == 'Guardian'
    assert post.call_args_list[0].kwargs['json']['reasoning']['enabled'] is False
    assert post.call_args_list[1].kwargs['json']['model'] == 'google/gemma-4-26b-a4b-it:free'


def test_completed_outline_and_draft_resume_without_provider_calls(tmp_path):
    (tmp_path / 'outline.json').write_text(json.dumps({'title': 'Guardian', 'character_bible': 'Mira', 'acts': ['act'] * 6}), encoding='utf-8')
    (tmp_path / 'draft.json').write_text(json.dumps([{'id': 1, 'duration': 12, 'start_state': 'river', 'end_state': 'river', 'prompt': 'Mira', 'narration': 'Mira brought the light home.'}]), encoding='utf-8')
    writer = StoryWriter({})
    writer.request = Mock(side_effect=AssertionError('Provider must not run for a saved complete draft'))
    result = writer.write('Guardian story', 'Anime', 12, cache_dir=tmp_path)
    assert len(result['shots']) == 1
    writer.request.assert_not_called()


def test_invalid_writer_batch_fails():
    writer = StoryWriter({})
    writer.request = Mock(side_effect=[{"character_bible": "Mira", "acts": [str(i) for i in range(6)]}, {"shots": []}, {"shots": []}])
    with pytest.raises(RuntimeError, match="valid narration"):
        writer.write('A guardian rescues a village', 'Anime', 24)


def test_comfy_validation_error_preserves_message(monkeypatch, tmp_path):
    response = Mock(ok=False, status_code=400, text='Required input is missing: model')
    monkeypatch.setattr('comfy_client.requests.post', lambda *a, **k: response)
    with pytest.raises(RuntimeError, match='Required input is missing'):
        ComfyClient().render({}, tmp_path / 'image.png', '.png')


def test_comfy_execution_error_is_not_success(monkeypatch, tmp_path):
    post = Mock(ok=True)
    post.json.return_value = {"prompt_id": "job-1"}
    history = Mock()
    history.json.return_value = {"job-1": {"status": {"status_str": "error", "messages": ["GPU failure"]}}}
    monkeypatch.setattr('comfy_client.requests.post', lambda *a, **k: post)
    monkeypatch.setattr('comfy_client.requests.get', lambda *a, **k: history)
    with pytest.raises(RuntimeError, match='GPU failure'):
        ComfyClient().render({}, tmp_path / 'image.png', '.png')
    assert not (tmp_path / 'image.png').exists()


def test_worker_thread_events_arrive_on_event_loop(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'ASSETS_DIR', tmp_path)
    async def check():
        queue = asyncio.Queue()
        studio.job_queues['event-check'] = [(queue, asyncio.get_running_loop())]
        worker = threading.Thread(target=studio.emit_event, args=('event-check', {"status_text": "Narration ready"}))
        worker.start()
        value = await asyncio.wait_for(queue.get(), 2)
        worker.join()
        assert value['status_text'] == 'Narration ready'
    asyncio.run(check())


def test_interrupted_job_can_be_identified(client, tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'ASSETS_DIR', tmp_path)
    root = tmp_path / 'jobs' / '123456abcdef'
    root.mkdir(parents=True)
    (root / 'status.json').write_text(json.dumps({"percent": 50}), encoding='utf-8')
    response = client.get('/api/jobs/123456abcdef')
    assert response.status_code == 200
    assert 'interrupted' in response.json()['error']
    assert client.get('/api/jobs/invalid').status_code == 404


def test_captions_cover_story_without_drift():
    value = ''.join(captions('One two three four five six seven eight nine ten eleven twelve thirteen fourteen', 12, offset=12, first_index=3))
    assert '00:00:12,000' in value
    assert '00:00:24,000' in value
    assert value.startswith('3\n')


def test_invalid_scene_is_never_silently_skipped(tmp_path):
    (tmp_path / 'scene_0001.mp4').write_bytes(b'broken')
    with pytest.raises(RuntimeError, match='invalid'):
        build_master_story(tmp_path)


def test_real_ffmpeg_timing_portrait_and_subtitles(tmp_path):
    image = tmp_path / 'art.png'
    Image.new('RGB', (320, 512), (35, 80, 120)).save(image)
    subtitles = tmp_path / 'input.srt'
    subtitles.write_text(''.join(captions('Mira found the light and brought it home.', 1)), encoding='utf-8')
    clips = []
    for index in range(2):
        clip = tmp_path / f'scene_{index:04d}.mp4'
        render_scene(image, None, 1, clip, '9:16', subtitles=subtitles)
        clips.append(clip)
    master = build_master_story(tmp_path, clips=clips, expected_duration=2)
    info = probe(master)
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    assert (video['width'], video['height']) == (432, 768)
    assert any(s['codec_type'] == 'audio' for s in info['streams'])
    assert abs(get_video_duration(master) - 2) < .15
    with pytest.raises(RuntimeError, match='duration verification'):
        build_master_story(tmp_path, clips=clips, expected_duration=20)


def test_legacy_camera_renderer_preserves_duration_without_audio(tmp_path, monkeypatch):
    image = tmp_path / 'art.png'
    Image.new('RGB', (64, 36), (35, 80, 120)).save(image)
    engine = RenderEngine(fps=12)
    monkeypatch.setattr(engine, '_parse_aspect_ratio', lambda ratio: (64, 36))
    result = engine.render_sequence([{"image_path": str(image), "duration": 5} for _ in range(3)], output_path=tmp_path / 'legacy.mp4', bpm_sync=True)
    assert result['duration'] == 15
    assert abs(get_video_duration(result['output_path']) - 15) < .15
