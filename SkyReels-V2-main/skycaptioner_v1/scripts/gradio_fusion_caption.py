import json
import argparse
import pandas as pd
import gradio as gr

from vllm import LLM, SamplingParams

from vllm_fusion_caption import StructuralCaptionDataset

parser = argparse.ArgumentParser()
parser.add_argument("--fusioncaptioner_model_path", default=None, type=str)
parser.add_argument("--tensor_parallel_size", type=int, default=2)
args = parser.parse_args()

example_input = """
{
    "subjects": [
        {
            "TYPES": {
                "type": "Human",
                "sub_type": "Woman"
            },
            "appearance": "Long, straight black hair with bangs, wearing a sparkling choker necklace and a dark-colored top or dress with a visible strap over her shoulder.",
            "action": "A woman wearing a sparkling choker necklace and earrings is sitting in a car, looking to her left and speaking. A man, dressed in a suit, is sitting next to her, attentively watching her.",
            "expression": "The individual in the video exhibits a neutral facial expression, characterized by slightly open lips and a gentle, soft-focus gaze. There are no noticeable signs of sadness or distress evident in their demeanor.",
            "position": "Seated in the foreground of the car, facing slightly to the right.",
            "is_main_subject": true
        },
        {
            "TYPES": {
                "type": "Human",
                "sub_type": "Man"
            },
            "appearance": "Short hair, wearing a dark-colored suit with a white shirt.",
            "action": "",
            "expression": "",
            "position": "Seated in the background of the car, facing the woman.",
            "is_main_subject": false
        }
    ],
    "shot_type": "close_up",
    "shot_angle": "eye_level",
    "shot_position": "side_view",
    "camera_motion": "",
    "environment": "Interior of a car with a dark color scheme.",
    "lighting": "Soft and natural lighting, suggesting daytime."
}
"""

class FusionCaptioner:
    def __init__(self, model_path, tensor_parallel_size):
        self.model = LLM(model=model_path,
            gpu_memory_utilization=0.9, 
            max_model_len=4096,
            tensor_parallel_size=tensor_parallel_size)    
        self.sampling_params = SamplingParams(
            temperature=0.1,
            max_tokens=512,
            stop=['\n\n']
        )    
        self.model_path = model_path

    def __call__(self, structural_caption, task='t2v'):
        if isinstance(structural_caption, dict):
            structural_caption = json.dumps(structural_caption, ensure_ascii=False)
        else:
            structural_caption = json.dumps(json.loads(structural_caption), ensure_ascii=False)
        meta = pd.DataFrame([structural_caption], columns=['structural_caption'])
        print(f'structural_caption: {structural_caption}')
        print(f'task: {task}')
        dataset = StructuralCaptionDataset(meta, self.model_path, task)
        _, fusion_by_llm, text, original_text, camera_movement = dataset[0]
        llm_original_texts = []     
        if not fusion_by_llm:     
            caption = original_text + " " + camera_movement
            return caption
        try:
            outputs = self.model.generate([text], self.sampling_params, use_tqdm=False)
            result = outputs[0].outputs[0].text
        except Exception as e:
            result = llm_original_texts
        
        llm_caption = result + " " + camera_movement
        return llm_caption

def main():
    fusion_captioner = FusionCaptioner(args.fusioncaptioner_model_path, args.tensor_parallel_size)

    def fusion_caption(structural_caption, task):
        caption = fusion_captioner(structural_caption, task)
        return caption
        
    with gr.Blocks() as demo:
        gr.Markdown(
            """
            <h1 style="text-align: center; font-size: 2em;">SkyCaptioner</h1>
            """,
            elem_id="header"
        )
        
        with gr.Row():
            with gr.Column(visible=True):
                with gr.Row():
                    json_input = gr.Code(
                        label="Structural Caption",
                        language="json",
                        lines=25,
                        interactive=True
                    )
                with gr.Row():
                    task_input = gr.Radio(
                        label="Task",
                        choices=["t2v", "i2v"],
                        value="t2v",
                        interactive=True
                    )                                  

            with gr.Column(visible=True):
                text_output = gr.Textbox(
                    label="Fusion Caption",
                    lines=25,
                    interactive=False,
                    autoscroll=True
                )

        gr.Button("Generate").click(
            fn=fusion_caption,
            inputs=[json_input, task_input],
            outputs=text_output
        )
        with gr.Row():
            gr.Examples(
                examples=[
                    [example_input, "t2v"],
                ],
                inputs=[json_input, task_input],
                label="Example Input"
            )
        demo.launch(
            server_name="0.0.0.0",
            server_port=7863,
            share=False
        )    

if __name__ == '__main__': 
    main()
