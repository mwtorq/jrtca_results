-- Rename sResults.TrialPlacements_GTGTimes to sResults.TrialPlacements_Times
-- Run against TrialResults database.

IF OBJECT_ID(N'sResults.TrialPlacements_GTGTimes', N'U') IS NOT NULL
   AND OBJECT_ID(N'sResults.TrialPlacements_Times', N'U') IS NULL
BEGIN
    EXEC sp_rename
        @objname = N'sResults.TrialPlacements_GTGTimes.TrialPlacements_GTGTimesID',
        @newname = N'TrialPlacements_TimesID',
        @objtype = N'COLUMN';

    IF EXISTS (
        SELECT 1 FROM sys.key_constraints
        WHERE name = N'PK_TrialPlacements_GTGTimes'
          AND parent_object_id = OBJECT_ID(N'sResults.TrialPlacements_GTGTimes')
    )
        EXEC sp_rename
            @objname = N'sResults.PK_TrialPlacements_GTGTimes',
            @newname = N'PK_TrialPlacements_Times',
            @objtype = N'OBJECT';

    IF EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name = N'FK_TrialPlacements_GTGTimes_TrialPlacementsID'
          AND parent_object_id = OBJECT_ID(N'sResults.TrialPlacements_GTGTimes')
    )
        EXEC sp_rename
            @objname = N'sResults.FK_TrialPlacements_GTGTimes_TrialPlacementsID',
            @newname = N'FK_TrialPlacements_Times_TrialPlacementsID',
            @objtype = N'OBJECT';

    EXEC sp_rename
        @objname = N'sResults.TrialPlacements_GTGTimes',
        @newname = N'TrialPlacements_Times',
        @objtype = N'OBJECT';

    PRINT 'Renamed sResults.TrialPlacements_GTGTimes to sResults.TrialPlacements_Times';
END
ELSE IF OBJECT_ID(N'sResults.TrialPlacements_Times', N'U') IS NOT NULL
    PRINT 'sResults.TrialPlacements_Times already exists; no rename needed.';
ELSE
BEGIN
    CREATE TABLE [sResults].[TrialPlacements_Times] (
        [TrialPlacements_TimesID] INT IDENTITY(1,1) NOT NULL,
        [TrialPlacementsID] INT NOT NULL,
        [Time] VARCHAR(255) NULL,
        CONSTRAINT [PK_TrialPlacements_Times] PRIMARY KEY ([TrialPlacements_TimesID]),
        CONSTRAINT [FK_TrialPlacements_Times_TrialPlacementsID] FOREIGN KEY ([TrialPlacementsID])
            REFERENCES [sResults].[TrialPlacements]([TrialPlacementsID])
    );
    PRINT 'Created sResults.TrialPlacements_Times';
END
