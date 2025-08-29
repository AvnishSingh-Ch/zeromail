# Requirements Document - Gmail True Deletion Feature

## Introduction

This feature enhances the Gmail IMAP Cleaner to provide true email deletion from Gmail accounts by implementing a multi-folder deletion strategy that addresses Gmail's unique All Mail behavior. Instead of attempting to delete from All Mail (which only removes labels), the system will delete emails from their actual source folders (INBOX, Sent, Drafts, etc.) to achieve permanent deletion.

## Requirements

### Requirement 1

**User Story:** As a Gmail user, I want to permanently delete old emails from my account, so that they are completely removed from all folders including All Mail.

#### Acceptance Criteria

1. WHEN user selects "true deletion" mode THEN system SHALL delete emails from their original folders (INBOX, Sent, Drafts, etc.) instead of All Mail
2. WHEN emails are deleted from original folders THEN they SHALL automatically disappear from All Mail view
3. WHEN deletion is complete THEN system SHALL verify emails are no longer present in any folder
4. IF user attempts to delete from All Mail THEN system SHALL warn about Gmail's behavior and offer true deletion alternative

### Requirement 2

**User Story:** As a Gmail user, I want to understand why All Mail deletion doesn't work as expected, so that I can make informed decisions about email management.

#### Acceptance Criteria

1. WHEN user selects All Mail folder THEN system SHALL display clear explanation of Gmail's All Mail behavior
2. WHEN All Mail deletion is attempted THEN system SHALL explain that only labels are removed, not actual emails
3. WHEN true deletion is offered THEN system SHALL explain the multi-folder approach and its benefits
4. WHEN deletion completes THEN system SHALL provide clear feedback about what actually happened

### Requirement 3

**User Story:** As a Gmail user, I want an automated multi-folder deletion process, so that I don't have to manually process each folder individually.

#### Acceptance Criteria

1. WHEN true deletion is selected THEN system SHALL automatically identify all relevant Gmail folders
2. WHEN processing folders THEN system SHALL delete emails from INBOX, Sent Mail, Drafts, and other user folders
3. WHEN processing each folder THEN system SHALL provide progress updates and deletion counts
4. WHEN all folders are processed THEN system SHALL provide a comprehensive summary of deletions across all folders

### Requirement 4

**User Story:** As a Gmail user, I want the option to preview which folders contain old emails before deletion, so that I can understand the scope of the operation.

#### Acceptance Criteria

1. WHEN true deletion is initiated THEN system SHALL scan all folders for emails matching the date criteria
2. WHEN scan is complete THEN system SHALL display a breakdown of email counts per folder
3. WHEN user confirms deletion THEN system SHALL proceed with multi-folder deletion
4. IF user cancels THEN system SHALL return to main menu without deleting any emails