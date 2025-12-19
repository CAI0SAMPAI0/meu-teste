from PySide6.QtCore import QThread, Signal
import os

class AutomationWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)  # (sucesso, mensagem)
    
    def __init__(self, userdir, target, mode, message=None, file_path=None):
        super().__init__()
        self.userdir = userdir
        self.target = target
        self.mode = mode
        self.message = message
        self.file_path = file_path
        
    def run(self):
        """Executa a automação em thread separada"""
        try:
            from core import automation
            
            def logger(msg):
                self.log_signal.emit(msg)
            
            automation.executar_envio(
                userdir=self.userdir,
                target=self.target,
                mode=self.mode,
                message=self.message,
                file_path=self.file_path,
                logger=logger
            )
            
            self.finished_signal.emit(True, "Automação concluída com sucesso!")
            
        except Exception as e:
            self.finished_signal.emit(False, f"Erro na automação: {str(e)}")