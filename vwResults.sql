CREATE OR ALTER VIEW [sResults].[vwResults] AS
SELECT TOP 10000000
	l.Year,
	l.TrialName,
	l.StartDate,
	l.EndDate,
	dv.DivisionName,
	c.ClassName,
	d.DogName,
	ISNULL(d.Sire, 'Not Available') AS Sire,
	ISNULL(d.Dam, 'Not Available') AS Dam,
	ISNULL(anc.Grandsire, 'Not Available') AS Grandsire,
	ISNULL(anc.Granddam, 'Not Available') AS Granddam,
	ISNULL(anc.GreatGrandsire, 'Not Available') AS GreatGrandsire,
	ISNULL(anc.GreatGranddam, 'Not Available') AS GreatGranddam,
	ISNULL(ss.Sibling, 'Not Available') AS Sibling,
	o.OwnerName,
	COALESCE(bo.OwnerName, br.OwnerName) AS BreederOwnerName,
	COALESCE(bo.City, br.City) AS BreederCity,
	COALESCE(bo.State, br.State) AS BreederState,
	COALESCE(bo.Email, br.Email) AS BreederEmail,
	COALESCE(bo.Phone, br.Phone) AS BreederPhone,
	COALESCE(bo.Website, br.Website) AS BreederWebsite,
	p.Result,
	p.Heat,
	p.Qtr,
	p.Semi,
	tc.EntryCount,
	pt.Time,
	nhc.NHC AS NHC,
	tcert.TrialCertificates AS TrialCertificates
FROM [TrialResults].[sResults].[TrialPlacements] (NOLOCK) p
JOIN [TrialResults].[sResults].[TrialList] (NOLOCK) l ON p.TrialListID = l.TrialListID
JOIN [TrialResults].[sResults].[TrialClass] (NOLOCK) tc ON p.TrialClassID = tc.TrialClassID
JOIN [TrialResults].[sResults].[Class] (NOLOCK) c ON tc.ClassID = c.ClassID
JOIN [TrialResults].[sResults].[Division] (NOLOCK) dv ON c.DivisionID = dv.DivisionID
JOIN [TrialResults].[sResults].[Dog] (NOLOCK) d ON p.DogID = d.DogID
LEFT JOIN [TrialResults].[sResults].[Owner] (NOLOCK) o ON d.OwnerID = o.OwnerID
LEFT JOIN [TrialResults].[sResults].[Breeder] (NOLOCK) br ON d.BreederID = br.BreederID
OUTER APPLY (
	SELECT TOP 1 o2.OwnerName, o2.City, o2.State, o2.Email, o2.Phone, o2.Website
	FROM [TrialResults].[sResults].[Owner] (NOLOCK) o2
	WHERE d.BreederID IS NOT NULL
	  AND o2.BreederID = d.BreederID
	ORDER BY o2.OwnerID
) bo
LEFT JOIN [TrialResults].[sResults].[TrialPlacements_Times] (NOLOCK) pt
	ON p.TrialPlacementsID = pt.TrialPlacementsID
OUTER APPLY (
	SELECT STRING_AGG(CAST(ss.RelatedDogName AS NVARCHAR(MAX)), ', ') AS Sibling
	FROM (
		(
			SELECT DISTINCT ss.RelatedDogName
			FROM [TrialResults].[sResults].[Relationship] ss (NOLOCK)
			WHERE d.DogID = ss.DogID
			  AND ISNULL(ss.RelationshipType, '') = 'Sibling'
		)
		UNION
		SELECT DISTINCT ss.RelatedDogName + ' (half)'
		FROM [TrialResults].[sResults].[Relationship] ss (NOLOCK)
		WHERE d.DogID = ss.DogID
		  AND ISNULL(ss.RelationshipType, '') LIKE '%Half%Sibling%'
	) ss
) ss
OUTER APPLY (
	SELECT
		STRING_AGG(CASE WHEN a.Kind = N'Grandsire' THEN a.RelatedDogName END, N', ')
			WITHIN GROUP (ORDER BY a.RelatedDogName) AS Grandsire,
		STRING_AGG(CASE WHEN a.Kind = N'Granddam' THEN a.RelatedDogName END, N', ')
			WITHIN GROUP (ORDER BY a.RelatedDogName) AS Granddam,
		STRING_AGG(CASE WHEN a.Kind = N'GreatGrandsire' THEN a.RelatedDogName END, N', ')
			WITHIN GROUP (ORDER BY a.RelatedDogName) AS GreatGrandsire,
		STRING_AGG(CASE WHEN a.Kind = N'GreatGranddam' THEN a.RelatedDogName END, N', ')
			WITHIN GROUP (ORDER BY a.RelatedDogName) AS GreatGranddam
	FROM (
		SELECT DISTINCT Kind, RelatedDogName
		FROM (
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
			SELECT N'GreatGrandsire', gp.Sire
			FROM [TrialResults].[sResults].[Dog] parent (NOLOCK)
			JOIN [TrialResults].[sResults].[Dog] gp (NOLOCK)
				ON gp.DogName IN (parent.Sire, parent.Dam)
			WHERE parent.DogName IN (d.Sire, d.Dam)
			UNION
			SELECT N'GreatGranddam', gp.Dam
			FROM [TrialResults].[sResults].[Dog] parent (NOLOCK)
			JOIN [TrialResults].[sResults].[Dog] gp (NOLOCK)
				ON gp.DogName IN (parent.Sire, parent.Dam)
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
-- One aggregated NHC string per dog (no row fan-out)
OUTER APPLY (
	SELECT STRING_AGG(x.Item, N' | ') WITHIN GROUP (ORDER BY x.SortYear, x.Item) AS NHC
	FROM (
		SELECT DISTINCT
			ISNULL(n.Year, 0) AS SortYear,
			CONCAT(
				ISNULL(CAST(n.Year AS nvarchar(10)), N'?'),
				N' ',
				ISNULL(n.CertificateType, N'NHC'),
				CASE WHEN NULLIF(LTRIM(RTRIM(n.Prey)), N'') IS NOT NULL
					THEN N' — ' + n.Prey ELSE N'' END,
				CASE WHEN NULLIF(LTRIM(RTRIM(n.JudgeName)), N'') IS NOT NULL
					THEN N' (Judge: ' + n.JudgeName + N')' ELSE N'' END
			) AS Item
		FROM [TrialResults].[sResults].[NHC] n (NOLOCK)
		WHERE (n.DogID IS NOT NULL AND n.DogID = d.DogID)
		   OR (n.DogID IS NULL AND n.DogName = d.DogName)
	) x
) nhc
-- One aggregated TrialCertificates string per dog (no row fan-out)
OUTER APPLY (
	SELECT STRING_AGG(x.Item, N' | ') WITHIN GROUP (ORDER BY x.SortYear, x.Item) AS TrialCertificates
	FROM (
		SELECT DISTINCT
			ISNULL(t.Year, 0) AS SortYear,
			CONCAT(
				ISNULL(CAST(t.Year AS nvarchar(10)), N'?'),
				N' ',
				ISNULL(t.CertificateType, N'Trial'),
				CASE WHEN NULLIF(LTRIM(RTRIM(t.TrialName)), N'') IS NOT NULL
					THEN N' @ ' + t.TrialName ELSE N'' END,
				CASE WHEN NULLIF(LTRIM(RTRIM(t.JudgeName)), N'') IS NOT NULL
					THEN N' (Judge: ' + t.JudgeName + N')' ELSE N'' END
			) AS Item
		FROM [TrialResults].[sResults].[TrialCertificates] t (NOLOCK)
		WHERE (t.DogID IS NOT NULL AND t.DogID = d.DogID)
		   OR (t.DogID IS NULL AND t.DogName = d.DogName)
	) x
) tcert
ORDER BY l.Year, l.StartDate, l.EndDate, l.TrialName, dv.DivisionName, c.ClassName, p.Result
