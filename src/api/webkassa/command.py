from abc import ABC, abstractclassmethod

class WebcassaCommand(ABC):
    
    @abstractclassmethod
    def handle():
        pass
    
    @abstractclassmethod
    def exc_callback():
        pass
    