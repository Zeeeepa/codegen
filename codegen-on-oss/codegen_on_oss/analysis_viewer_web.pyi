from typing import Any, Dict, List, Optional, Union
import gradio as gr

class AnalysisViewerWeb:
    def __init__(self) -> None: ...
    def create_interface(self) -> gr.Blocks: ...
    def launch(
        self, 
        share: bool = False, 
        server_name: str = "127.0.0.1", 
        server_port: Optional[int] = None,
        inbrowser: bool = True
    ) -> None: ...

