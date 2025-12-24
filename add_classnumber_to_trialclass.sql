-- Add ClassNumber column to TrialClass table
-- This column stores the class number (e.g., "Class 1", "Class 2") for a specific trial class

USE TrialResults;
GO

-- Check if column already exists before adding
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('sResults.TrialClass') 
    AND name = 'ClassNumber'
)
BEGIN
    ALTER TABLE [sResults].[TrialClass]
    ADD [ClassNumber] VARCHAR(50) NULL;
    
    PRINT 'ClassNumber column added to TrialClass table';
END
ELSE
BEGIN
    PRINT 'ClassNumber column already exists in TrialClass table';
END
GO
