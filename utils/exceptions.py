import sys

class MissingBinaryError(Exception):
    pass

class PipelineTimeoutError(Exception):
    pass

def handle_pipeline_exception(exception: Exception, status_callback=None) -> bool:
    match exception:
        case MissingBinaryError() as soft_err:
            if status_callback:
                status_callback("binary_error", {"details": str(soft_err)})
            sys.exit(1)

        case PipelineTimeoutError() as timeout_err:
            if status_callback:
                status_callback("timeout_error", {"details": str(timeout_err)})
            return False

        case FileNotFoundError() as fnf_err:
            if status_callback:
                status_callback("file_error", {"details": f"Temporary file missing: {fnf_err}"})
            return False

        case Exception() as unhandled_err:
            if status_callback:
                status_callback("unknown_error", {"details": f"Unexpected crash: {unhandled_err}"})
            return True