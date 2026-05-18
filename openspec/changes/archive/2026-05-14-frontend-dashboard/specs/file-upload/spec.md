## ADDED Requirements

### Requirement: Multi-file upload capability
The file upload component SHALL support selecting multiple files simultaneously via browse dialog and drag-and-drop.

#### Scenario: Select files via browse
- **WHEN** user clicks upload button and selects multiple files
- **THEN** all selected files are added to the upload queue

#### Scenario: Drag and drop files
- **WHEN** user drags files over the upload zone
- **THEN** upload zone is highlighted with visual feedback

#### Scenario: Drop files into zone
- **WHEN** user drops files onto the upload zone
- **THEN** all dropped files are added to the upload queue

### Requirement: Supported file types
The upload component SHALL accept log files (.txt), images (.png, .jpg, .jpeg), and documents (.pdf) for VLLM analysis.

#### Scenario: Valid log file selection
- **WHEN** user selects a .txt file
- **THEN** file is accepted and added to queue

#### Scenario: Valid image selection
- **WHEN** user selects .png, .jpg, or .jpeg files
- **THEN** files are accepted and added to queue

#### Scenario: Invalid file type rejection
- **WHEN** user selects unsupported file type (e.g., .exe, .zip)
- **THEN** file is rejected with clear error message explaining supported types

### Requirement: Upload queue visualization
The upload component SHALL display a queue showing each file's name, size, type, and upload progress.

#### Scenario: Display queue items
- **WHEN** files are added to queue
- **THEN** each file displays with name, type icon, and file size

#### Scenario: Upload progress indicator
- **WHEN** file is uploading
- **THEN** progress bar shows completion percentage

#### Scenario: Remove file from queue
- **WHEN** user clicks remove button on a queue item
- **THEN** file is removed from upload queue

### Requirement: Upload status feedback
The upload component SHALL provide clear visual feedback for pending, uploading, success, and error states.

#### Scenario: Upload success state
- **WHEN** file upload completes successfully
- **THEN** success icon and message appear; file linked to analysis session

#### Scenario: Upload error state
- **WHEN** file upload fails
- **THEN** error icon and message appear with retry option

#### Scenario: Upload pending state
- **WHEN** file is waiting in queue
- **THEN** pending indicator shows file hasn't started uploading yet
