import unittest
from unittest.mock import patch, MagicMock
import subprocess

# Import dell'handler, delle eccezioni custom e dei moduli della tua app
from utils.exceptions import handle_pipeline_exception, PipelineTimeoutError
from utils import validate_plan
from generation_main import ui_status_logger

class TestPipelineExceptionHandling(unittest.TestCase):

    def setUp(self):
        """Configurazione iniziale per ciascun test."""
        print(f"\n {'='*10} AVVIO: {self._testMethodName} {'='*10}")
        self.mock_callback = MagicMock()
        
        self.domain = "domain.pddl"
        self.problem = "problem.pddl"
        self.plan = "plan_file.pddl"

    def tearDown(self):
        """Pulizia post-test."""
        print(f" {'='*10} FINE: {self._testMethodName} {'='*10}\n")

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_timeout_error_skips_seed(self, mock_run, mock_exists):
        """
        TEST 1: Verifica che un timeout si converta in PipelineTimeoutError,
        venga loggato correttamente e ritorni False per saltare il seed.
        """
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["Validate"], timeout=10)

        print("[VERBOSO] Eseguo validate_plan aspettandomi il PipelineTimeoutError custom...")
        
        # Verifichiamo che validate_plan converta correttamente l'eccezione nativa in quella custom
        with self.assertRaises(PipelineTimeoutError) as context:
            validate_plan(self.domain, self.problem, self.plan)
            
        caught_exception = context.exception
        print(f"[VERBOSO] Eccezione custom sollevata correttamente: {type(caught_exception).__name__}")

        print("[VERBOSO] Passo l'eccezione custom all'handler globale...")
        should_abort = handle_pipeline_exception(caught_exception, self.mock_callback)
        print(f"[VERBOSO] Risposta handler: should_abort = {should_abort}")

        # Verifiche di consistenza
        self.assertFalse(should_abort)
        self.mock_callback.assert_called_once_with("timeout_error", {"details": "VAL validation timed out after 10s."})
        print("[OK] Test Timeout superato.")

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_unknown_error_aborts_loop(self, mock_run, mock_exists):
        """
        TEST 2: Verifica che un errore imprevisto (OSError) superi la funzione
        e faccia ritornare True all'handler per interrompere il loop.
        """
        mock_exists.return_value = True
        mock_run.side_effect = OSError(28, "No space left on device")

        print("[VERBOSO] Eseguo validate_plan aspettandomi che l'OSError rimanga invariato...")
        
        with self.assertRaises(OSError) as context:
            validate_plan(self.domain, self.problem, self.plan)
            
        caught_exception = context.exception
        print(f"[VERBOSO] Eccezione di sistema propagata: {type(caught_exception).__name__} -> {caught_exception}")

        print("[VERBOSO] Passo l'OSError imprevisto al paracadute dell'handler globale...")
        should_abort = handle_pipeline_exception(caught_exception, self.mock_callback)
        print(f"[VERBOSO] Risposta handler: should_abort = {should_abort}")

        # Verifiche di consistenza
        self.assertTrue(should_abort)
        self.mock_callback.assert_called_once_with("unknown_error", {"details": "Unexpected crash: [Errno 28] No space left on device"})
        print("[OK] Test Errore Imprevisto superato.")

    def test_ui_logger_output_consistency(self):
        """
        TEST 3: Ispezione visiva dei formati di stampa del logger reale.
        """
        print("[VERBOSO] Emissione log reali sul terminale tramite ui_status_logger:")
        print("-" * 50)
        ui_status_logger("timeout_error", {"details": "VAL validation timed out after 10s."})
        print("-" * 50)
        ui_status_logger("unknown_error", {"details": "Unexpected crash: [Errno 28] No space left on device"})
        print("-" * 50)
        print("[OK] Ispezione visiva completata.")

if __name__ == '__main__':
    unittest.main(verbosity=2)