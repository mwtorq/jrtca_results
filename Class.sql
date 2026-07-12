SELECT [ClassID]
      ,[DivisionID]
      ,[ClassName]
      ,[SectionID]
  FROM [TrialResults].[sResults].[Class] (NOLOCK)
  ORDER BY ClassName

  --delete [TrialResults].[sResults].[Class]
