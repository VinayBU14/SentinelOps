from fastapi import HTTPException, status

class SentinelOpsException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class FileTooLargeException(SentinelOpsException):
    def __init__(self, max_bytes: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum allowed size of {max_bytes} bytes (10 MB)."
        )

class UnsupportedFileTypeException(SentinelOpsException):
    def __init__(self, detail: str = "Unsupported file type. Please upload a .csv or .json file."):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=detail
        )

class InvalidFileStructureException(SentinelOpsException):
    def __init__(self, detail: str = "Invalid file structure or missing required columns."):
        super().__init__(
            status_code=422,
            detail=detail
        )

class BatchNotFoundException(SentinelOpsException):
    def __init__(self, batch_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import batch with ID '{batch_id}' was not found."
        )

class BatchNotReadyException(SentinelOpsException):
    def __init__(self, detail: str = "Batch is not ready for risk analysis."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
