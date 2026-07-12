--SELECT [TrialPlacementsID]
--      ,[TrialListID]
--      ,[TrialClassID]
--      ,[DogID]
--      ,[Result]
--  FROM [TrialResults].[sResults].[TrialPlacements]

DECLARE @Name VARCHAR(100) = '%Waelterman%'
DECLARE @Name1 VARCHAR(100) = '%Waelterman%'

SELECT DISTINCT l.Year,l.TrialName,l.StartDate,l.EndDate,dv.DivisionName,c.ClassName,d.DogName,d.Sire,d.Dam,sgs.Grandsire as Grandsire,sgd.Granddam AS Granddam,sggs.GreatGrandsire as GreatGrandsire,sggd.GreatGranddam AS GreatGranddam,ss.Sibling AS Sibling,o.OwnerName,p.Result,tc.EntryCount,pt.Time
FROM [TrialResults].[sResults].[TrialPlacements] (NOLOCK) p
JOIN [TrialResults].[sResults].[TrialList] (NOLOCK) l ON p.TrialListID=l.TrialListID
JOIN [TrialResults].[sResults].[TrialClass] (NOLOCK) tc ON p.TrialClassID=tc.TrialClassID
JOIN [TrialResults].[sResults].[Class] (NOLOCK) c ON tc.ClassID=c.ClassID
JOIN [TrialResults].[sResults].[Division] (NOLOCK) dv ON c.DivisionID=dv.DivisionID
JOIN [TrialResults].[sResults].[Dog] (NOLOCK) d ON p.DogID=d.DogID
LEFT JOIN [TrialResults].[sResults].[Owner] (NOLOCK) o ON d.OwnerID=o.OwnerID
LEFT JOIN [TrialResults].[sResults].[TrialPlacements_Times] (NOLOCK) pt ON p.TrialPlacementsID=pt.TrialPlacementsID
OUTER APPLY (SELECT STRING_AGG(ss.RelatedDogName,', ') AS Sibling FROM ((SELECT DISTINCT ss.RelatedDogName FROM [TrialResults].[sResults].[Relationship] ss (NOLOCK) WHERE d.DogID=ss.DogID AND ISNULL(ss.RelationshipType,'')='Sibling') UNION SELECT DISTINCT ss.RelatedDogName + ' (half)' FROM [TrialResults].[sResults].[Relationship] ss (NOLOCK) WHERE d.DogID=ss.DogID AND ISNULL(ss.RelationshipType,'') LIKE '%Half%Sibling%') ss) ss
OUTER APPLY (SELECT STRING_AGG(sgs.RelatedDogName,', ') AS Grandsire FROM (SELECT DISTINCT sgs.RelatedDogName FROM [TrialResults].[sResults].[Relationship] sgs (NOLOCK) WHERE d.DogID=sgs.DogID AND ISNULL(sgs.RelationshipType,'') IN ('','Grandsire')) sgs) sgs
OUTER APPLY (SELECT STRING_AGG(sgd.RelatedDogName,', ') AS Granddam FROM (SELECT DISTINCT sgd.RelatedDogName FROM [TrialResults].[sResults].[Relationship] sgd (NOLOCK) WHERE d.DogID=sgd.DogID AND ISNULL(sgd.RelationshipType,'') IN ('','Granddam')) sgd) sgd
OUTER APPLY (SELECT STRING_AGG(sggs.RelatedDogName,', ') AS GreatGrandsire FROM (SELECT DISTINCT sggs.RelatedDogName FROM [TrialResults].[sResults].[Relationship] sggs (NOLOCK) WHERE d.DogID=sggs.DogID AND ISNULL(sggs.RelationshipType,'') IN ('','Great-Grandsire')) sggs) sggs
OUTER APPLY (SELECT STRING_AGG(sggd.RelatedDogName,', ') AS GreatGranddam FROM (SELECT DISTINCT sggd.RelatedDogName FROM [TrialResults].[sResults].[Relationship] sggd (NOLOCK) WHERE d.DogID=sggd.DogID AND ISNULL(sggd.RelationshipType,'') IN ('','Great-Granddam')) sggd) sggd
WHERE (o.OwnerName LIKE @Name OR o.OwnerName LIKE @Name1)
--WHERE pt.Time IS NOT NULL
--WHERE l.Year IN (2023,2025) AND l.TrialName LIKE '%JRTCC%'
--WHERE (l.TrialName LIKE '%Earthdogs%' OR l.TrialName LIKE '%MOE%') AND (Year IN (2012,2014,2019) OR Year BETWEEN 2014 AND 2018)
--AND d.DogName LIKE '%Blanca%'-- AND dv.DivisionName LIKE '%GROUND%'
--AND d.DogName LIKE '%Skeeter%'
--AND l.Year>=2016
--WHERE l.TrialListID IN (1678,1679,1680)
--WHERE l.TrialName LIKE '%JRTCA National Trial%'
--WHERE c.ClassID=548884
ORDER BY l.Year,l.StartDate,l.EndDate,l.TrialName,dv.DivisionName,c.ClassName,p.Result

SELECT p.Result,COUNT(*)
FROM [TrialResults].[sResults].[TrialPlacements] (NOLOCK) p
JOIN [TrialResults].[sResults].[TrialList] (NOLOCK) l ON p.TrialListID=l.TrialListID
LEFT JOIN [TrialResults].[sResults].[TrialClass] (NOLOCK) tc ON p.TrialClassID=tc.TrialClassID
LEFT JOIN [TrialResults].[sResults].[Class] (NOLOCK) c ON tc.ClassID=c.ClassID
LEFT JOIN [TrialResults].[sResults].[Division] (NOLOCK) dv ON c.DivisionID=dv.DivisionID
LEFT JOIN [TrialResults].[sResults].[Dog] (NOLOCK) d ON p.DogID=d.DogID
LEFT JOIN [TrialResults].[sResults].[Owner] (NOLOCK) o ON d.OwnerID=o.OwnerID
WHERE o.OwnerName LIKE @Name
--AND l.Year>=2016
--WHERE l.TrialName LIKE '%National Trial%'
GROUP BY p.Result
ORDER BY p.Result

SELECT l.Year,p.Result,COUNT(*)
FROM [TrialResults].[sResults].[TrialPlacements] (NOLOCK) p
JOIN [TrialResults].[sResults].[TrialList] (NOLOCK) l ON p.TrialListID=l.TrialListID
LEFT JOIN [TrialResults].[sResults].[TrialClass] (NOLOCK) tc ON p.TrialClassID=tc.TrialClassID
LEFT JOIN [TrialResults].[sResults].[Class] (NOLOCK) c ON tc.ClassID=c.ClassID
LEFT JOIN [TrialResults].[sResults].[Division] (NOLOCK) dv ON c.DivisionID=dv.DivisionID
LEFT JOIN [TrialResults].[sResults].[Dog] (NOLOCK) d ON p.DogID=d.DogID
LEFT JOIN [TrialResults].[sResults].[Owner] (NOLOCK) o ON d.OwnerID=o.OwnerID
WHERE o.OwnerName LIKE @Name
--AND l.Year>=2016
--WHERE l.TrialName LIKE '%National Trial%'
GROUP BY p.Result,l.Year
ORDER BY l.Year,p.Result
