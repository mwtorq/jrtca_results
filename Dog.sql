SELECT [DogID]
      ,[DogName]
      ,d.[OwnerID]
      ,[Sire]
      ,[Dam]
      ,[Sex]
      ,o.OwnerName
  FROM [TrialResults].[sResults].[Dog] (NOLOCK) d
  LEFT JOIN [TrialResults].[sResults].[Owner] (NOLOCK) O ON d.OwnerID=o.OwnerID
  --WHERE o.OwnerName LIKE '%Waelterman%'
  --where dogname like '%keelyn%' or dogname like '%rel%blanca%'
  --where sire is not null or dam is not null
  --where dogname like '%hunter%ro%xie%'

  --delete [TrialResults].[sResults].[Dog]