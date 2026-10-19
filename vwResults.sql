CREATE OR ALTER VIEW [sResults].[vwResults] AS
	SELECT TOP 10000000 l.Year,l.TrialName,l.StartDate,l.EndDate,dv.DivisionName,c.ClassName,d.DogName,ISNULL(d.Sire,'Not Available') AS Sire,ISNULL(d.Dam,'Not Available') AS Dam,ISNULL(anc.Grandsire,'Not Available') AS Grandsire,ISNULL(anc.Granddam,'Not Available') AS Granddam,ISNULL(anc.GreatGrandsire,'Not Available') as GreatGrandsire,ISNULL(anc.GreatGranddam,'Not Available') AS GreatGranddam,ISNULL(ss.Sibling,'Not Available') AS Sibling,o.OwnerName,p.Result,tc.EntryCount,pt.Time
	FROM [TrialResults].[sResults].[TrialPlacements] (NOLOCK) p
	JOIN [TrialResults].[sResults].[TrialList] (NOLOCK) l ON p.TrialListID=l.TrialListID
	JOIN [TrialResults].[sResults].[TrialClass] (NOLOCK) tc ON p.TrialClassID=tc.TrialClassID
	JOIN [TrialResults].[sResults].[Class] (NOLOCK) c ON tc.ClassID=c.ClassID
	JOIN [TrialResults].[sResults].[Division] (NOLOCK) dv ON c.DivisionID=dv.DivisionID
	JOIN [TrialResults].[sResults].[Dog] (NOLOCK) d ON p.DogID=d.DogID
	LEFT JOIN [TrialResults].[sResults].[Owner] (NOLOCK) o ON d.OwnerID=o.OwnerID
	LEFT JOIN [TrialResults].[sResults].[TrialPlacements_Times] (NOLOCK) pt ON p.TrialPlacementsID=pt.TrialPlacementsID
	OUTER APPLY (SELECT STRING_AGG(CAST(ss.RelatedDogName AS NVARCHAR(MAX)),', ') AS Sibling FROM ((SELECT DISTINCT ss.RelatedDogName FROM [TrialResults].[sResults].[Relationship] ss (NOLOCK) WHERE d.DogID=ss.DogID AND ISNULL(ss.RelationshipType,'')='Sibling') UNION SELECT DISTINCT ss.RelatedDogName + ' (half)' FROM [TrialResults].[sResults].[Relationship] ss (NOLOCK) WHERE d.DogID=ss.DogID AND ISNULL(ss.RelationshipType,'') LIKE '%Half%Sibling%') ss) ss
	OUTER APPLY (
		SELECT
			STRING_AGG(CASE WHEN a.Kind = N'Grandsire' THEN a.RelatedDogName END, N', ') WITHIN GROUP (ORDER BY a.RelatedDogName) AS Grandsire,
			STRING_AGG(CASE WHEN a.Kind = N'Granddam' THEN a.RelatedDogName END, N', ') WITHIN GROUP (ORDER BY a.RelatedDogName) AS Granddam,
			STRING_AGG(CASE WHEN a.Kind = N'GreatGrandsire' THEN a.RelatedDogName END, N', ') WITHIN GROUP (ORDER BY a.RelatedDogName) AS GreatGrandsire,
			STRING_AGG(CASE WHEN a.Kind = N'GreatGranddam' THEN a.RelatedDogName END, N', ') WITHIN GROUP (ORDER BY a.RelatedDogName) AS GreatGranddam
		FROM (
			SELECT DISTINCT Kind, RelatedDogName
			FROM (
				-- Both grandparents: sire's parents and dam's parents
				SELECT N'Grandsire' AS Kind, sire.Sire AS RelatedDogName
				FROM [TrialResults].[sResults].[Dog] sire (NOLOCK)
				WHERE sire.DogName = d.Sire
				UNION
				SELECT N'Grandsire', dam.Sire
				FROM [TrialResults].[sResults].[Dog] dam (NOLOCK)
				WHERE dam.DogName = d.Dam
				UNION
				SELECT N'Granddam', sire.Dam
				FROM [TrialResults].[sResults].[Dog] sire (NOLOCK)
				WHERE sire.DogName = d.Sire
				UNION
				SELECT N'Granddam', dam.Dam
				FROM [TrialResults].[sResults].[Dog] dam (NOLOCK)
				WHERE dam.DogName = d.Dam
				UNION
				SELECT rel.RelationshipType, rel.RelatedDogName
				FROM [TrialResults].[sResults].[Relationship] rel (NOLOCK)
				WHERE rel.DogID = d.DogID
				  AND rel.RelationshipType IN (N'Grandsire', N'Granddam')
				UNION
				-- All four great-grandsires / great-granddams via each grandparent
				SELECT N'GreatGrandsire', gp.Sire
				FROM [TrialResults].[sResults].[Dog] parent (NOLOCK)
				JOIN [TrialResults].[sResults].[Dog] gp (NOLOCK) ON gp.DogName IN (parent.Sire, parent.Dam)
				WHERE parent.DogName IN (d.Sire, d.Dam)
				UNION
				SELECT N'GreatGranddam', gp.Dam
				FROM [TrialResults].[sResults].[Dog] parent (NOLOCK)
				JOIN [TrialResults].[sResults].[Dog] gp (NOLOCK) ON gp.DogName IN (parent.Sire, parent.Dam)
				WHERE parent.DogName IN (d.Sire, d.Dam)
				UNION
				SELECT CASE rel.RelationshipType
					WHEN N'Great-grandsire' THEN N'GreatGrandsire'
					WHEN N'Great-granddam' THEN N'GreatGranddam'
				END, rel.RelatedDogName
				FROM [TrialResults].[sResults].[Relationship] rel (NOLOCK)
				WHERE rel.DogID = d.DogID
				  AND rel.RelationshipType IN (N'Great-grandsire', N'Great-granddam')
			) raw
			WHERE NULLIF(LTRIM(RTRIM(raw.RelatedDogName)), N'') IS NOT NULL
			  AND raw.RelatedDogName <> N'Not Available'
			  AND raw.Kind IS NOT NULL
		) a
	) anc
	ORDER BY l.Year,l.StartDate,l.EndDate,l.TrialName,dv.DivisionName,c.ClassName,p.Result
