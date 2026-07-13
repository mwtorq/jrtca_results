CREATE OR ALTER VIEW [sResults].[vwResults] AS
	SELECT TOP 10000000 l.Year,l.TrialName,l.StartDate,l.EndDate,dv.DivisionName,c.ClassName,d.DogName,ISNULL(d.Sire,'Not Available') AS Sire,ISNULL(d.Dam,'Not Available') AS Dam,ISNULL(sgs.Grandsire,'Not Available') AS Grandsire,ISNULL(sgd.Granddam,'Not Available') AS Granddam,ISNULL(sggs.GreatGrandsire,'Not Available') as GreatGrandsire,ISNULL(sggd.GreatGranddam,'Not Available') AS GreatGranddam,ISNULL(ss.Sibling,'Not Available') AS Sibling,o.OwnerName,p.Result,tc.EntryCount,pt.Time
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
	ORDER BY l.Year,l.StartDate,l.EndDate,l.TrialName,dv.DivisionName,c.ClassName,p.Result
