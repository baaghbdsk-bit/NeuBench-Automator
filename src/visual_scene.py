try:
    from manim import *
except ImportError:
    class Scene:
        pass
import config

class NeuBenchScene(Scene):
    def construct(self):
        title = Text("NeuBench AI", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))
