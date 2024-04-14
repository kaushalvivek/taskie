'''
Writer is an intelligent service that can re-write any text given context and instructions for the re-write.
'''

class Writer:
    def __init__(self, model):
        self.model = model

    def summarise(self, context: str, tone: str, input: str) -> str:
        pass

    def get_title_for(self, context: str, tone: str, input: str) -> str:
        pass