from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """
    Abstrakte Basisklasse für alle LLM-Adapter.
    Garantiert, dass jeder Adapter die gleiche Struktur liefert.
    """

    @abstractmethod
    def send(self, prompt: str) -> dict:
        """
        Sendet einen Prompt an das Modell und gibt ein standardisiertes 
        Dictionary mit Antwort und Metriken zurück.
        """
        pass