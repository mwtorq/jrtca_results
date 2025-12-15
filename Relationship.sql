SELECT r.[RelationshipID]
      ,r.[DogID]
      ,d.[DogName]
      ,o.[OwnerName]
      ,r.[RelatedDogID]
      ,r.[RelatedDogName]
      ,r.[RelationshipType]
      ,r.[ViaDogName]
      ,r.[RelatedDogSex]
  FROM [TrialResults].[sResults].[Relationship] r
  JOIN [TrialResults].[sResults].[Dog] d ON R.DogID=d.DogID
  JOIN [TrialResults].[sResults].[Owner] o ON d.OwnerID=o.OwnerID
  --WHERE o.OwnerName LIKE '%Waelterman%'
  --WHERE d.DogID=769 AND r.RelatedDogID=736
  --WHERE d.DogID=1011 AND r.RelatedDogID=346
  --WHERE d.DogID=46 AND r.RelatedDogID=1288
  ORDER BY d.DogName

SELECT r.[DogID]
      ,d.[DogName]
      ,COUNT(*)
  FROM [TrialResults].[sResults].[Relationship] r
  JOIN [TrialResults].[sResults].[Dog] d ON R.DogID=d.DogID
  GROUP BY r.[DogID],d.[DogName]
  ORDER BY COUNT(*) DESC

SELECT r.[DogID]
      ,d.[DogName]
      ,r.[RelationshipType]
      ,COUNT(*)
  FROM [TrialResults].[sResults].[Relationship] r
  JOIN [TrialResults].[sResults].[Dog] d ON R.DogID=d.DogID
  GROUP BY r.[DogID],d.[DogName],r.[RelationshipType]
  ORDER BY COUNT(*) DESC

SELECT r.[DogID]
      ,r.[RelatedDogID]
      --,r.[RelationshipType]
      ,COUNT(*)
  FROM [TrialResults].[sResults].[Relationship] r
WHERE r.RelatedDogID IS NOT NULL
GROUP BY r.DogID,r.RelatedDogID--,r.[RelationshipType]
HAVING COUNT(*)>1