class ReportError(Exception):
    """Base exception for report generation errors."""
    pass


class AggregationError(ReportError):
    """Error during finding aggregation."""
    pass


class TemporalAnalysisError(ReportError):
    """Error during temporal analysis."""
    pass


class InvalidInputError(ReportError):
    """Invalid input data provided."""
    def __init__(self, message: str, field: str):
        self.field = field
        super().__init__(message)
