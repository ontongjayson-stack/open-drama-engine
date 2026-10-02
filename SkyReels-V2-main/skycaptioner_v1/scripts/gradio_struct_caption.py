import json
import argparse
import pandas as pd
import gradio as gr
from vllm import LLM, SamplingParams
from vllm_struct_caption import VideoTextDataset


class StructCaptioner:
    def __init__(self, model_path, tensor_parallel_size):
        self.model = LLM(model=model_path,
            gpu_memory_utilization=0.6, 
            max_model_len=31920,
            tensor_parallel_size=tensor_parallel_size)    

        self.model_path = model_path
        self.sampling_params = SamplingParams(temperature=0.05, max_tokens=2048)

    def __call__(self, video_path):
        meta = pd.DataFrame([video_path], columns=['path'])
        dataset = VideoTextDataset(meta, self.model_path)
        item = dataset[0]['input']
        batch_user_inputs = [{
            'prompt': item['prompt'],
            'multi_modal_data':{'video': item['multi_modal_data']['video'][0]},
        }]
        outputs = self.model.generate(batch_user_inputs, self.sampling_params, use_tqdm=False)
        caption = outputs[0].outputs[0].text
        caption = json.loads(caption)
        caption = json.dumps(caption, indent=4, ensure_ascii=False)
        return caption

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skycaptioner_model_path", required=True, type=str)
    parser.add_argument("--tensor_parallel_size", type=int, default=2)
    args = parser.parse_args()

    struct_captioner = StructCaptioner(args.skycaptioner_model_path, args.tensor_parallel_size)
    def generate_caption(video_path):
        caption = struct_captioner(video_path)
        return caption
    
    with gr.Blocks() as demo:
        gr.Markdown(
            """
            <h1 style="text-align: center; font-size: 2em;">SkyCaptioner</h1>
            """,
            elem_id="header"
        )
        
        with gr.Row():
            with gr.Column(visible=True, scale=0.5):
                with gr.Row():
                    video_input = gr.Video(
                        label="Upload Video",
                        interactive=True,
                        format="mp4", 
                    )                                

            with gr.Column(visible=True):
                json_output = gr.Code(
                    label="Caption",
                    language="json",
                    lines=25,
                    interactive=False
                )

        gr.Button("Generate").click(
            fn=generate_caption,
            inputs=video_input,
            outputs=json_output
        )   

        gr.Examples(
            examples=[
                ["./examples/data/1.mp4"],
                ["./examples/data/2.mp4"],
            ],
            inputs=video_input,
            label="Example Videos"
        )    

        demo.launch(
            server_name="0.0.0.0",
            server_port=7862,
            share=False
        )

if __name__ == '__main__': 
    main()
