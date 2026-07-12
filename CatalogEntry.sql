SELECT [CatalogEntryID]
      ,[Year]
      ,[EntryNumber]
      ,[DogID]
      ,[DogName]
      ,[OwnerID]
      ,[Sire]
      ,[Dam]
      ,[Sex]
      ,[ClassID]
      ,[ClassName]
  FROM [TrialResults].[sResults].[CatalogEntry]

  SELECT Year,COUNT(*)  FROM [TrialResults].[sResults].[CatalogEntry] GROUP BY Year ORDER BY Year
  --delete [TrialResults].[sResults].[CatalogEntry] where year=2019