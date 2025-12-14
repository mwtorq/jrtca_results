USE [TrialData]
GO

/****** Object:  StoredProcedure [sJRTCA].[spBestCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spBestCleanup] AS
	update sjrtca.trialplacements set result='Champion'
	from sjrtca.trialplacements tp
	join sjrtca.trialclass tc on tp.trialclassid=tc.trialclassid
	join sjrtca.class c on tc.classid=c.classid
	where tp.result='Best' and c.classname in
	('ADULT RACING CHAMPION & RESERVE 10 UP TO 12.5"',
	'ADULT RACING CHAMPION & RESERVE 10 UP TO 12.5".',
	'ADULT RACING CHAMPION & RESERVE OVER 12.5" UP TO 15".',
	'BEST 4 UP TO 6 MONTH PUPPY & RESERVE',
	'BEST 4-6 MONTH PUPPY & RESERVE',
	'BEST 4-6 MONTH PUPPY&RESERVE',
	'Best 4-6 Month Pup & Reserve',
	'BEST OPEN TERRIER & RESERVE',
	'BEST OPEN TERRIER CONFORMATION',
	'BEST OPEN TERRIER& RESERVE',
	'BEST WORKING TERRIER & RESERVE',
	'Dog Pups, 4 up to 6 months',
	'PUPPY CONFORMATION CHAMPION & RESERVE',
	'PUPPY CONFORMATION CHAMPIONSHIP',
	'PUPPY RACING CHAMPION & RESERVE OVER 12.5" UP TO 15"',
	'PUPPY RACING CHAMPION & RESERVE OVER 12.5" UP TO 15".',
	'PUPPY RACING CHAMPION & RESERVE UP TO 12.5"',
	'PUPPY RACING CHAMPION & RESERVE UP TO 12.5".',
	'RALLY-O CHAMPION AND RESERVE',
	'SENIOR RACING CHAMPION & RESERVE 10 UP TO 12.5"',
	'SENIOR RACING CHAMPION & RESERVE 10 UP TO 12.5".',
	'SENIOR RACING CHAMPION & RESERVE OVER 12.5" UP TO 15',
	'SMALL TERRIER HIGH JUMP BEST & RESERVE',
	'SMALL VETERAN/SENIOR TERRIER LURE COURSING BEST & RESERVE',
	'TALL TERRIER HIGH JUMP BEST & RESERVE',
	'TALL TERRIER LURE COURSING BEST & RESERVE',
	'TALL VETERAN/SENIOR TERRIER LURE COURSING BEST & RESERVE',
	'VETERANS RACING CHAMPION & RESERVE 10 UP TO 12.5".',
	'VETERANS RACING CHAMPION & RESERVE OVER 12.5" UP TO 15".',
	'WORKING TERRIER CHAMPION & RESERVE',
	'SENIOR RACING CHAMPION & RESERVE OVER 12Ωî UP TO 15?.',
	'BEST JRTCA WORKING TERRIER',
	'JRTCA WORKING TERRIER CONFORMATION CHAMPION & RESERVE',
	'JRTCC NATIONAL TRIAL CONFORMATION CHAMPION & RESERVE',
	'OBEDIENCE BEST HIGH SCORE & RESERVE',
	'ALL AROUND VETERAN HIGH POINT CHAMPION & RESERVE',
	'OPEN TERRIER CONFORMATION CHAMPIONSHIP',
	'Best 4 up to 6 months Puppy Champion & Reserve',
	'BEST OPEN ADULT TERRIER',
	'BEST OPEN TERRIER AND RESERVE',
	'PUPPY CONFORMATION CHAMPION AND RESERVE',
	'BEST PUP AND RESERVE',
	'BEST PUP & RESERVE'
	)

	select * from sjrtca.trialplacements tp
	join sjrtca.trialclass tc on tp.trialclassid=tc.trialclassid
	join sjrtca.class c on tc.classid=c.classid
	where tp.result='Best'
GO

/****** Object:  StoredProcedure [sJRTCA].[spBlankOwnerCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spBlankOwnerCleanup] AS
select
distinct 'UPDATE [sJRTCA].trialplacements SET dogid=' + CAST(d1.dogid as varchar(10)) + ' WHERE trialplacementsid=' + cast(tp.trialplacementsid as varchar(10)) + '--' + d.dogname + ' from ' + d1.dogname + ', owner: ' + o1.ownername + ' from ' + o.ownername,d.dogname,d1.dogname,o1.ownername--,tp1.result--,*
from [sJRTCA].trialplacements tp
left join [sJRTCA].trialclass tc on tp.trialclassid=tc.trialclassid
left join [sJRTCA].class c on tc.classid=c.classid
left join sjrtca.triallist tl on tp.triallistid=tl.triallistid
left join sall.dog d on tp.dogid=d.dogid
left join sall.dog d1 on d.dogname=d1.dogname
left join sall.owner o on d.ownerid=o.ownerid
left join sall.owner o1 on d1.ownerid=o1.ownerid
left join [sJRTCA].trialplacements tp1 on tp.triallistid=tp1.triallistid and d1.dogid=tp1.dogid
left join [sJRTCA].trialclass tc1 on tp1.trialclassid=tc1.trialclassid
left join [sJRTCA].class c1 on tc1.classid=c1.classid and c.divisionid=c1.divisionid
where d.dogname<>'' and o.ownername='' and d.ownerid<>d1.ownerid --and tl.trialname in ('jrtca national trial','jrtcc national trial') and tp.result in ('champion','best','reserve') and tp1.result not in ('champion','best','reserve')
and tp.trialplacementsid<>tp1.trialplacementsid --and d1.dogid in (
order by d.dogname
GO

/****** Object:  StoredProcedure [sJRTCA].[spClassCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spClassCleanup] (@MatchScore FLOAT=.9) AS
	EXEC [sJRTCA].[spFuzzyMatch_Class] @MatchScore

	; WITH MinMatch AS (
		SELECT DISTINCT 
			m.FirstClassID,m.FirstClassName,m.DivisionID,Min(m.MatchScore) OVER (PARTITION BY FirstClassID,FirstClassName) AS MatchScore,COUNT(m.FirstClassID) OVER (PARTITION BY tc.classid,m.divisionid) AS ClassCount
		FROM sJRTCA.Class_TempMatch m
		JOIN sJRTCA.trialclass tc on m.firstclassid=tc.classid 
		JOIN sJRTCA.class c on tc.classid=c.classid and m.divisionid=c.divisionid
		where firstClassid<>secondClassid
	)
	SELECT DISTINCT 
		'UPDATE ' + DB_NAME() + '.sJRTCA.TrialClass SET ClassID=' + CAST(m.FirstClassID AS VARCHAR(25)) + ' WHERE ClassID=' + CAST(t.SecondClassID AS VARCHAR(25)) + '--' + m.FirstClassName + ' from ' + t.SecondClassName + ' (' + d.DivisionName + ')' AS Stmt,m.FirstClassID,m.FirstClassName,t.SecondClassID,t.SecondClassName,m.DivisionID,m.MatchScore,m.ClassCount,ROW_NUMBER() OVER (ORDER BY m.ClassCount DESC) AS RowNumber
	FROM MinMatch m
	JOIN sJRTCA.Division d ON m.DivisionID=d.DivisionID
	JOIN sJRTCA.Class_TempMatch t ON m.FirstClassID=t.FirstClassID AND m.MatchScore=t.MatchScore
	where t.firstClassid<>t.secondClassid and t.firstclassname not like 'class%' and t.secondclassname not like 'class%'
	UNION
	SELECT TOP 1 
		'delete ' + DB_NAME() + '.sJRTCA.Class where classid not in (select distinct classid from sJRTCA.trialclass)' AS Stmt,NULL,NULL,NULL,NULL,NULL,NULL,NULL,999999 AS RowNumber
	order by RowNumber,m.ClassCount DESC;
GO

/****** Object:  StoredProcedure [sJRTCA].[spDivisionCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spDivisionCleanup] AS
	select 'update ' + DB_NAME() + '.sjrtca.class set divisionid=' + cast(divisionid as varchar(10)) + ' where divisionid=' + cast(divisionid as varchar(10)) + '--' + divisionname AS Stmt,ROW_NUMBER() OVER (ORDER BY DivisionName) AS RowNumber
	from sjrtca.division
	UNION
	SELECT TOP 1
		'delete ' + DB_NAME() + '.sJRTCA.Division where divisionid not in (select distinct divisionid from sJRTCA.class)' AS Stmt,9999999 AS RowNumber
	order by RowNumber,Stmt
GO

/****** Object:  StoredProcedure [sJRTCA].[spDogCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spDogCleanup] (@MatchScore FLOAT=.9,@DogName varchar(255)=NULL,@Year INT=NULL,@ResultsCount INT=40) AS
	EXEC [sJRTCA].[spFuzzyMatch_Dog] @MatchScore,@DogName,@Year

	; WITH MinMatch AS (
		SELECT DISTINCT 
			m.FirstDogID,m.FirstDogName,d.Sire AS FirstDogSire,d.Dam AS FirstDogDam,d1.Sire AS SecondDogSire,d1.Dam AS SecondDogDam,m.OwnerName,Min(m.MatchScore) OVER (PARTITION BY FirstDogID,FirstDogName) AS MatchScore,COUNT(*) OVER (PARTITION BY p.dogid) AS DogResultsCount
		FROM sJRTCA.Dog_TempMatch m
		LEFT JOIN sAll.Dog d ON m.FirstDogID=d.DogID
		LEFT JOIN sAll.Dog d1 ON m.SecondDogID=d1.DogID
		JOIN sJRTCA.trialplacements p on m.firstDogid=p.Dogid
		where firstDogid<>secondDogid
	)
	SELECT DISTINCT 
		'UPDATE ' + DB_NAME() + '.sJRTCA.TrialPlacements SET DogID=' + CAST(m.FirstDogID AS VARCHAR(25)) + ' WHERE DogID=' + CAST(t.SecondDogID AS VARCHAR(25)) + '--' + m.FirstDogName + ' ' + ISNULL('(' + m.FirstDogSire + 'x' + m.FirstDogDam + ')','') + ' from ' + t.SecondDogName + ISNULL(' (' + d.Sire + 'x' + d.Dam + ')',''),m.FirstDogID,m.FirstDogName,m.FirstDogSire,m.FirstDogDam,m.MatchScore,m.OwnerName,t.SecondDogID,t.SecondDogName,d.Sire AS SecondDogSire,d.Dam AS SecondDogDam,m.MatchScore,m.DogResultsCount,ROW_NUMBER() OVER (ORDER BY m.DogResultsCount DESC) AS RowNumber
	FROM MinMatch m
	JOIN sJRTCA.Dog_TempMatch t ON m.FirstDogID=t.FirstDogID AND m.MatchScore=t.MatchScore
	LEFT JOIN sAll.Dog d ON t.SecondDogID=d.DogID
	where t.firstDogid<>t.secondDogid AND m.DogResultsCount>=@ResultsCount
	UNION
	SELECT TOP 1
		'delete ' + DB_NAME() + '.sall.dog where dogid not in (select distinct dogid from ' + DB_NAME() + '.sjrtca.trialplacements) and ownerid not in (1) and sire is null and dam is null and dogid not in (select damid from t.sall.dog union select sireid from t.sall.dog)',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,999999 AS RowNumber
	order by m.FirstDogName,RowNumber,m.DogResultsCount DESC;
GO

/****** Object:  StoredProcedure [sJRTCA].[spFixSplitClasses]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [sJRTCA].[spFixSplitClasses] (@WrongClassName VARCHAR(255),@CorrectedEntry VARCHAR(255),@RightClassName VARCHAR(255),@TrialListID INT) AS

DECLARE @TrialClassID INT

select DISTINCT @TrialClassID=tc.TrialClassID
from sjrtca.trialplacements tp 
join sjrtca.trialclass tc on tp.trialclassid=tc.trialclassid
join sjrtca.class c on tc.classid=c.classid
join sall.dog d on tp.dogid=d.dogid
where tp.triallistid=@TrialListID and c.classname in (@RightClassName)

IF @TrialClassID IS NULL
	select DISTINCT @TrialClassID=(tc.TrialClassID-1)
	from sjrtca.trialplacements tp 
	join sjrtca.trialclass tc on tp.trialclassid=tc.trialclassid
	join sjrtca.class c on tc.classid=c.classid
	join sall.dog d on tp.dogid=d.dogid
	where tp.triallistid=@TrialListID and c.classname in (@WrongClassName)

--SELECT @TrialClassID 

EXEC [sJRTCA].[spInsertTrialPlacement] @Result=@CorrectedEntry,@TrialListID=@TrialListID,@TrialClassID=@TrialClassID

UPDATE sJRTCA.TrialPlacements
SET TrialClassID=@TrialClassID
from sjrtca.trialplacements tp 
left join sjrtca.trialclass tc on tp.trialclassid=tc.trialclassid
left join sjrtca.class c on tc.classid=c.classid
left join sall.dog d on tp.dogid=d.dogid
where tp.triallistid=@TrialListID and c.classname in (@WrongClassName)

delete t.sjrtca.trialclass where trialclassid=(SELECT TrialClassID FROM sJRTCA.TrialClass tc JOIN sJRTCA.Class c ON tc.ClassID=c.ClassID WHERE c.ClassName=@WrongClassName)
delete t.sjrtca.class where classid=(SELECT ClassID FROM sJRTCA.Class WHERE ClassName=@WrongClassName)

select *
from t.sjrtca.trialplacements tp 
join t.sjrtca.trialclass tc on tp.trialclassid=tc.trialclassid
join t.sjrtca.class c on tc.classid=c.classid
join t.sall.dog d on tp.dogid=d.dogid
where tp.triallistid=@TrialListID and (c.classname in (@WrongClassName,@RightClassName) or tc.TrialClassID=@TrialClassID)
GO

/****** Object:  StoredProcedure [sJRTCA].[spFuzzyMatch_Class]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


 
--Use this code to execute the procedure once you've created it: EXEC [TestDB].[dbo].[FuzzyMatch_Company] @MatchScore = .8
 
CREATE procedure [sJRTCA].[spFuzzyMatch_Class] (
 
@MatchScore float = .8 --You can change this every time you execute the stored procedure, but here I've set it to default to an 80% match or greater
 
) AS
 
TRUNCATE TABLE [sJRTCA].[Class_TempMatch]
INSERT INTO [sJRTCA].[Class_TempMatch]
 
SELECT ListA.ClassID AS FirstClassID
    ,ListA.ClassName AS FirstClassName
    ,ListB.ClassID AS SecondClassID
    ,ListB.ClassName AS SecondClassName
	,ListA.DivisionID
    ,MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName,  0, 1.0, @MatchScore) as MatchScore
 
FROM (
    SELECT [ClassID]
          ,[ClassName]
          ,[DivisionID]
    FROM [sJRTCA].[Class]
) ListA
 
JOIN (
    SELECT [ClassID]
          ,[ClassName]
		  ,comp.DivisionID
    FROM [sJRTCA].[Class] comp
 
    LEFT JOIN [sJRTCA].[Class_FinalMatch] fin ON comp.ClassID = fin.SecondClassID
    WHERE fin.SecondClassID IS NULL
) ListB
 
ON MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName, 0, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID
WHERE 
	(ListA.ClassName LIKE '%4 up to 6%' AND ListB.ClassName LIKE '%4 up to 6%') OR
	(ListA.ClassName LIKE '%6 up to 9%' AND ListB.ClassName LIKE '%6 up to 9%') OR
	(ListA.ClassName LIKE '%6 up to 12%' AND ListB.ClassName LIKE '%6 up to 12%') OR
	(ListA.ClassName LIKE '%9 up to 12%' AND ListB.ClassName LIKE '%9 up to 12%') OR
	(ListA.ClassName LIKE '%4 up to 12%' AND ListB.ClassName LIKE '%4 up to 12%') OR
	(ListA.ClassName LIKE '%4-6%' AND ListB.ClassName LIKE '%4-6%') OR
	(ListA.ClassName LIKE '%6-9%' AND ListB.ClassName LIKE '%6-9%') OR
	(ListA.ClassName LIKE '%6-12%' AND ListB.ClassName LIKE '%6-12%') OR
	(ListA.ClassName LIKE '%9-12%' AND ListB.ClassName LIKE '%9-12%') OR
	(ListA.ClassName LIKE '%4-12%' AND ListB.ClassName LIKE '%4-12%') OR
	(ListA.ClassName LIKE '%Agil% I,%' AND ListB.ClassName LIKE '%Agil% I,%') OR
	(ListA.ClassName LIKE '%Agil% II,%' AND ListB.ClassName LIKE '%Agil% II,%') OR
	(ListA.ClassName LIKE '%Agil% III,%' AND ListB.ClassName LIKE '%Agil% III,%') OR
	(ListA.ClassName LIKE '%Agil% I %' AND ListB.ClassName LIKE '%Agil% I %') OR
	(ListA.ClassName LIKE '%Agil% II %' AND ListB.ClassName LIKE '%Agil% II %') OR
	(ListA.ClassName LIKE '%Agil% III %' AND ListB.ClassName LIKE '%Agil% III %') OR
	(ListA.ClassName LIKE '%Agil% I' AND ListB.ClassName LIKE '%Agil% I') OR
	(ListA.ClassName LIKE '%Agil% II' AND ListB.ClassName LIKE '%Agil% II') OR
	(ListA.ClassName LIKE '%Agil% III' AND ListB.ClassName LIKE '%Agil% III') OR
	(ListA.ClassName LIKE '%Jumpers% I %' AND ListB.ClassName LIKE '%Jumpers% I %') OR
	(ListA.ClassName LIKE '%Jumpers% II %' AND ListB.ClassName LIKE '%Jumpers% II %') OR
	(ListA.ClassName LIKE '%Jumpers% III %' AND ListB.ClassName LIKE '%Jumpers% III %') OR
	(ListA.ClassName NOT LIKE '%4 up to 6%' AND ListB.ClassName NOT LIKE '%4 up to 6%' AND 
	ListA.ClassName NOT LIKE '%6 up to 9%' AND ListB.ClassName NOT LIKE '%6 up to 9%' AND 
	ListA.ClassName NOT LIKE '%6 up to 12%' AND ListB.ClassName NOT LIKE '%6 up to 12%' AND 
	ListA.ClassName NOT LIKE '%9 up to 12%' AND ListB.ClassName NOT LIKE '%9 up to 12%' AND 
	ListA.ClassName NOT LIKE '%4 up to 12%' AND ListB.ClassName NOT LIKE '%4 up to 12%' AND 
	ListA.ClassName NOT LIKE '%4-6%' AND ListB.ClassName NOT LIKE '%4-6%' AND 
	ListA.ClassName NOT LIKE '%6-9%' AND ListB.ClassName NOT LIKE '%6-9%' AND 
	ListA.ClassName NOT LIKE '%6-12%' AND ListB.ClassName NOT LIKE '%6-12%' AND 
	ListA.ClassName NOT LIKE '%9-12%' AND ListB.ClassName NOT LIKE '%9-12%' AND 
	ListA.ClassName NOT LIKE '%4-12%' AND ListB.ClassName NOT LIKE '%4-12%' AND
	ListA.ClassName NOT LIKE '%Agil% I,%' AND ListB.ClassName NOT LIKE '%Agil% I,%' AND
	ListA.ClassName NOT LIKE '%Agil% II.%' AND ListB.ClassName NOT LIKE '%Agil% II,%' AND
	ListA.ClassName NOT LIKE '%Agil% III,%' AND ListB.ClassName NOT LIKE '%Agil% III,%' AND
	ListA.ClassName NOT LIKE '%Agil% I %' AND ListB.ClassName NOT LIKE '%Agil% I %' AND
	ListA.ClassName NOT LIKE '%Agil% II %' AND ListB.ClassName NOT LIKE '%Agil% II %' AND
	ListA.ClassName NOT LIKE '%Agil% III %' AND ListB.ClassName NOT LIKE '%Agil% III %' AND
	ListA.ClassName NOT LIKE '%Agil% I' AND ListB.ClassName NOT LIKE '%Agil% I' AND
	ListA.ClassName NOT LIKE '%Agil% II' AND ListB.ClassName NOT LIKE '%Agil% II' AND
	ListA.ClassName NOT LIKE '%Agil% III' AND ListB.ClassName NOT LIKE '%Agil% III' AND
	ListA.ClassName NOT LIKE '%Jumpers% I %' AND ListB.ClassName NOT LIKE '%Jumpers% I %' AND
	ListA.ClassName NOT LIKE '%Jumpers% II %' AND ListB.ClassName NOT LIKE '%Jumpers% II %' AND
	ListA.ClassName NOT LIKE '%Jumpers% III %' AND ListB.ClassName NOT LIKE '%Jumpers% III %')


 
--UNION
 
----The following are exact copies of the above code, except the matching algorithms are changed in each
 
--SELECT ListA.ClassID AS FirstClassID
--    ,ListA.ClassName AS FirstClassName
--    ,ListB.ClassID AS SecondClassID
--    ,ListB.ClassName AS SecondClassName
--	,ListA.DivisionID
--    ,MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName,  1, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [ClassID]
--          ,[ClassName]
--		  ,[DivisionID]
--    FROM [sJRTCA].[Class]
--) ListA
 
--JOIN (
--    SELECT [ClassID]
--          ,[ClassName]
--		  ,comp.DivisionID
--    FROM [sJRTCA].[Class] comp
 
--    LEFT JOIN [sJRTCA].[Class_FinalMatch] fin ON comp.ClassID = fin.SecondClassID
--    WHERE fin.SecondClassID IS NULL
--) ListB
 
--ON MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName, 1, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID
 
--UNION
 
--SELECT ListA.ClassID AS FirstClassID
--    ,ListA.ClassName AS FirstClassName
--    ,ListB.ClassID AS SecondClassID
--    ,ListB.ClassName AS SecondClassName
--	,ListA.DivisionID
--    ,MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName,  2, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [ClassID]
--          ,[ClassName]
--		  ,[DivisionID]
--    FROM [sJRTCA].[Class]
--) ListA
 
--JOIN (
--    SELECT [ClassID]
--          ,[ClassName]
--		  ,comp.DivisionID
--    FROM [sJRTCA].[Class] comp
 
--    LEFT JOIN [sJRTCA].[Class_FinalMatch] fin ON comp.ClassID = fin.SecondClassID
--    WHERE fin.SecondClassID IS NULL
--) ListB
 
--ON MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName, 2, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID
 
--UNION
 
--SELECT ListA.ClassID AS FirstClassID
--    ,ListA.ClassName AS FirstClassName
--    ,ListB.ClassID AS SecondClassID
--    ,ListB.ClassName AS SecondClassName
--	,ListA.DivisionID
--    ,MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName,  3, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [ClassID]
--          ,[ClassName]
--		  ,[DivisionID]
--    FROM [sJRTCA].[Class]
--) ListA
 
--JOIN (
--    SELECT [ClassID]
--          ,[ClassName]
--		  ,comp.DivisionID
--    FROM [sJRTCA].[Class] comp
 
--    LEFT JOIN [sJRTCA].[Class_FinalMatch] fin ON comp.ClassID = fin.SecondClassID
--    WHERE fin.SecondClassID IS NULL
--) ListB
 
--ON MDS.mdq.Similarity(ListA.ClassName, ListB.ClassName, 3, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID
GO

/****** Object:  StoredProcedure [sJRTCA].[spFuzzyMatch_Division]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



 
--Use this code to execute the procedure once you've created it: EXEC [TestDB].[dbo].[FuzzyMatch_Company] @MatchScore = .8
 
CREATE procedure [sJRTCA].[spFuzzyMatch_Division] (
 
@MatchScore float = .8 --You can change this every time you execute the stored procedure, but here I've set it to default to an 80% match or greater
 
) AS
 
TRUNCATE TABLE [sJRTCA].[Division_TempMatch]
INSERT INTO [sJRTCA].[Division_TempMatch]
 
SELECT ListA.DivisionID AS FirstDivisionID
    ,ListA.DivisionName AS FirstDivisionName
    ,ListB.DivisionID AS SecondDivisionID
    ,ListB.DivisionName AS SecondDivisionName
    ,MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName,  0, 1.0, @MatchScore) as MatchScore
 
FROM (
    SELECT [DivisionID]
          ,[DivisionName]
    FROM [sJRTCA].[Division]
) ListA
 
JOIN (
    SELECT [DivisionID]
          ,[DivisionName]
    FROM [sJRTCA].[Division] comp
 
    LEFT JOIN [sJRTCA].[Division_FinalMatch] fin ON comp.DivisionID = fin.SecondDivisionID
    WHERE fin.SecondDivisionID IS NULL
) ListB
 
ON MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName, 0, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID
 
--UNION
 
----The following are exact copies of the above code, except the matching algorithms are changed in each
 
--SELECT ListA.DivisionID AS FirstDivisionID
--    ,ListA.DivisionName AS FirstDivisionName
--    ,ListB.DivisionID AS SecondDivisionID
--    ,ListB.DivisionName AS SecondDivisionName
--	,ListA.DivisionID
--    ,MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName,  1, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [DivisionID]
--          ,[DivisionName]
--		  ,[DivisionID]
--    FROM [sJRTCA].[Division]
--) ListA
 
--JOIN (
--    SELECT [DivisionID]
--          ,[DivisionName]
--		  ,comp.DivisionID
--    FROM [sJRTCA].[Division] comp
 
--    LEFT JOIN [sJRTCA].[Division_FinalMatch] fin ON comp.DivisionID = fin.SecondDivisionID
--    WHERE fin.SecondDivisionID IS NULL
--) ListB
 
--ON MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName, 1, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID
 
--UNION
 
--SELECT ListA.DivisionID AS FirstDivisionID
--    ,ListA.DivisionName AS FirstDivisionName
--    ,ListB.DivisionID AS SecondDivisionID
--    ,ListB.DivisionName AS SecondDivisionName
--	,ListA.DivisionID
--    ,MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName,  2, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [DivisionID]
--          ,[DivisionName]
--		  ,[DivisionID]
--    FROM [sJRTCA].[Division]
--) ListA
 
--JOIN (
--    SELECT [DivisionID]
--          ,[DivisionName]
--		  ,comp.DivisionID
--    FROM [sJRTCA].[Division] comp
 
--    LEFT JOIN [sJRTCA].[Division_FinalMatch] fin ON comp.DivisionID = fin.SecondDivisionID
--    WHERE fin.SecondDivisionID IS NULL
--) ListB
 
--ON MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName, 2, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID
 
--UNION
 
--SELECT ListA.DivisionID AS FirstDivisionID
--    ,ListA.DivisionName AS FirstDivisionName
--    ,ListB.DivisionID AS SecondDivisionID
--    ,ListB.DivisionName AS SecondDivisionName
--	,ListA.DivisionID
--    ,MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName,  3, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [DivisionID]
--          ,[DivisionName]
--		  ,[DivisionID]
--    FROM [sJRTCA].[Division]
--) ListA
 
--JOIN (
--    SELECT [DivisionID]
--          ,[DivisionName]
--		  ,comp.DivisionID
--    FROM [sJRTCA].[Division] comp
 
--    LEFT JOIN [sJRTCA].[Division_FinalMatch] fin ON comp.DivisionID = fin.SecondDivisionID
--    WHERE fin.SecondDivisionID IS NULL
--) ListB
 
--ON MDS.mdq.Similarity(ListA.DivisionName, ListB.DivisionName, 3, 1.0, @MatchScore) >= @MatchScore AND ListA.DivisionID=ListB.DivisionID

GO

/****** Object:  StoredProcedure [sJRTCA].[spFuzzyMatch_Dog]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


 
--Use this code to execute the procedure once you've created it: EXEC [TestDB].[dbo].[FuzzyMatch_Company] @MatchScore = .8
 
CREATE procedure [sJRTCA].[spFuzzyMatch_Dog] (
 
@MatchScore float = .8 --You can change this every time you execute the stored procedure, but here I've set it to default to an 80% match or greater
,@DogName varchar(255)
,@Year INT=NULL
 
) AS
 
TRUNCATE TABLE [sJRTCA].[Dog_TempMatch]
INSERT INTO [sJRTCA].[Dog_TempMatch]
 
SELECT ListA.DogID AS FirstDogID
    ,ListA.DogName AS FirstDogName
    ,ListB.DogID AS SecondDogID
    ,ListB.DogName AS SecondDogName
	,ListA.OwnerName
    ,MDS.mdq.Similarity(ListA.DogName, ListB.DogName,  0, 1.0, @MatchScore) as MatchScore
 
FROM (
    SELECT [DogID]
          ,[DogName]
		  ,o.OwnerName
    FROM [sAll].[Dog] d
	JOIN [sAll].[Owner] o ON d.OwnerID=o.OwnerID
	WHERE (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%') AND (@Year IS NULL OR DogID IN (SELECT DogID FROM sJRTCA.TrialPlacements p JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
) ListA
 
JOIN (
    SELECT [DogID]
          ,[DogName]
		  ,o.OwnerName
    FROM [sAll].[Dog] d
	JOIN [sAll].[Owner] o ON d.OwnerID=o.OwnerID 
    LEFT JOIN [sJRTCA].[Dog_FinalMatch] fin ON d.DogID = fin.SecondDogID
    WHERE fin.SecondDogID IS NULL
	AND (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%') AND (@Year IS NULL OR DogID IN (SELECT DogID FROM sJRTCA.TrialPlacements p JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
) ListB
 
ON MDS.mdq.Similarity(ListA.DogName, ListB.DogName, 0, 1.0, @MatchScore) >= @MatchScore AND ListA.OwnerName=ListB.OwnerName
 
--UNION
 
----The following are exact copies of the above code, except the matching algorithms are changed in each
 
--SELECT ListA.DogID AS FirstDogID
--    ,ListA.DogName AS FirstDogName
--    ,ListB.DogID AS SecondDogID
--    ,ListB.DogName AS SecondDogName
--    ,MDS.mdq.Similarity(ListA.DogName, ListB.DogName,  1, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [DogID]
--          ,[DogName]
--    FROM [sAll].[Dog]
--    WHERE (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%')
--) ListA
 
--JOIN (
--    SELECT [DogID]
--          ,[DogName]
--    FROM [sAll].[Dog] comp
 
--    LEFT JOIN [sJRTCA].[Dog_FinalMatch] fin ON comp.DogID = fin.SecondDogID
--    WHERE fin.SecondDogID IS NULL
--    AND (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%')
--) ListB
 
--ON MDS.mdq.Similarity(ListA.DogName, ListB.DogName, 1, 1.0, @MatchScore) >= @MatchScore
 
--UNION
 
--SELECT ListA.DogID AS FirstDogID
--    ,ListA.DogName AS FirstDogName
--    ,ListB.DogID AS SecondDogID
--    ,ListB.DogName AS SecondDogName
--    ,MDS.mdq.Similarity(ListA.DogName, ListB.DogName,  2, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [DogID]
--          ,[DogName]
--    FROM [sALL].[Dog]
--    WHERE (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%')
--) ListA
 
--JOIN (
--    SELECT [DogID]
--          ,[DogName]
--    FROM [sAll].[Dog] comp
 
--    LEFT JOIN [sJRTCA].[Dog_FinalMatch] fin ON comp.DogID = fin.SecondDogID
--    WHERE fin.SecondDogID IS NULL
--    AND (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%')
--) ListB
 
--ON MDS.mdq.Similarity(ListA.DogName, ListB.DogName, 2, 1.0, @MatchScore) >= @MatchScore
 
--UNION
 
--SELECT ListA.DogID AS FirstDogID
--    ,ListA.DogName AS FirstDogName
--    ,ListB.DogID AS SecondDogID
--    ,ListB.DogName AS SecondDogName
--    ,MDS.mdq.Similarity(ListA.DogName, ListB.DogName,  3, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [DogID]
--          ,[DogName]
--    FROM [sAll].[Dog]
--    WHERE (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%')
--) ListA
 
--JOIN (
--    SELECT [DogID]
--          ,[DogName]
--    FROM [sAll].[Dog] comp
 
--    LEFT JOIN [sJRTCA].[Dog_FinalMatch] fin ON comp.DogID = fin.SecondDogID
--    WHERE fin.SecondDogID IS NULL
--    AND (@DogName IS NULL OR DogName LIKE '%' + @DogName + '%')
--) ListB
 
--ON MDS.mdq.Similarity(ListA.DogName, ListB.DogName, 3, 1.0, @MatchScore) >= @MatchScore
 
GO

/****** Object:  StoredProcedure [sJRTCA].[spFuzzyMatch_Owner]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


 
--Use this code to execute the procedure once you've created it: EXEC [TestDB].[dbo].[FuzzyMatch_Company] @MatchScore = .8
 
CREATE procedure [sJRTCA].[spFuzzyMatch_Owner] (
 
@MatchScore float = .8 --You can change this every time you execute the stored procedure, but here I've set it to default to an 80% match or greater
,@OwnerName varchar(255)
,@Year INT=NULL
 
) AS
 
TRUNCATE TABLE [sJRTCA].[Owner_TempMatch]
INSERT INTO [sJRTCA].[Owner_TempMatch]
 
SELECT ListA.OwnerID AS FirstOwnerID
    ,ListA.OwnerName AS FirstOwnerName
    ,ListB.OwnerID AS SecondOwnerID
    ,ListB.OwnerName AS SecondOwnerName
    ,MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName,  0, 1.0, @MatchScore) as MatchScore
 
FROM (
    SELECT [OwnerID]
          ,[OwnerName]
    FROM [sAll].[Owner]
	WHERE (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
) ListA
 
JOIN (
    SELECT [OwnerID]
          ,[OwnerName]
    FROM [sAll].[Owner] comp
 
    LEFT JOIN [sJRTCA].[Owner_FinalMatch] fin ON comp.OwnerID = fin.SecondOwnerID
    WHERE fin.SecondOwnerID IS NULL
	AND (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
) ListB
 
ON MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName, 0, 1.0, @MatchScore) >= @MatchScore
 
--UNION
 
----The following are exact copies of the above code, except the matching algorithms are changed in each
 
--SELECT ListA.OwnerID AS FirstOwnerID
--    ,ListA.OwnerName AS FirstOwnerName
--    ,ListB.OwnerID AS SecondOwnerID
--    ,ListB.OwnerName AS SecondOwnerName
--    ,MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName,  1, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [OwnerID]
--          ,[OwnerName]
--    FROM [sAll].[Owner]
--	WHERE (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
--) ListA
 
--JOIN (
--    SELECT [OwnerID]
--          ,[OwnerName]
--    FROM [sAll].[Owner] comp
 
--    LEFT JOIN [sJRTCA].[Owner_FinalMatch] fin ON comp.OwnerID = fin.SecondOwnerID
--    WHERE fin.SecondOwnerID IS NULL
--	AND (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
--) ListB
 
--ON MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName, 1, 1.0, @MatchScore) >= @MatchScore
 
--UNION
 
--SELECT ListA.OwnerID AS FirstOwnerID
--    ,ListA.OwnerName AS FirstOwnerName
--    ,ListB.OwnerID AS SecondOwnerID
--    ,ListB.OwnerName AS SecondOwnerName
--    ,MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName,  2, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [OwnerID]
--          ,[OwnerName]
--    FROM [sALL].[Owner]
--	WHERE (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
--) ListA
 
--JOIN (
--    SELECT [OwnerID]
--          ,[OwnerName]
--    FROM [sAll].[Owner] comp
 
--    LEFT JOIN [sJRTCA].[Owner_FinalMatch] fin ON comp.OwnerID = fin.SecondOwnerID
--    WHERE fin.SecondOwnerID IS NULL
--	AND (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
--) ListB
 
--ON MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName, 2, 1.0, @MatchScore) >= @MatchScore
 
--UNION
 
--SELECT ListA.OwnerID AS FirstOwnerID
--    ,ListA.OwnerName AS FirstOwnerName
--    ,ListB.OwnerID AS SecondOwnerID
--    ,ListB.OwnerName AS SecondOwnerName
--    ,MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName,  3, 1.0, @MatchScore) as MatchScore
 
--FROM (
--    SELECT [OwnerID]
--          ,[OwnerName]
--    FROM [sAll].[Owner]
--	WHERE (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
--) ListA
 
--JOIN (
--    SELECT [OwnerID]
--          ,[OwnerName]
--    FROM [sAll].[Owner] comp
 
--    LEFT JOIN [sJRTCA].[Owner_FinalMatch] fin ON comp.OwnerID = fin.SecondOwnerID
--    WHERE fin.SecondOwnerID IS NULL
--	AND (@OwnerName IS NULL OR OwnerName LIKE '%' + @ownername + '%') AND (@Year IS NULL OR OwnerID IN (SELECT OwnerID FROM sAll.Dog d JOIN sJRTCA.TrialPlacements p ON d.DogID=p.DogID JOIN sJRTCA.TrialClass tc ON p.TrialClassID=tc.TrialClassID JOIN sJRTCA.TrialList l ON tc.TrialListID=l.TrialListID WHERE l.Year=@Year))
--) ListB
 
--ON MDS.mdq.Similarity(ListA.OwnerName, ListB.OwnerName, 3, 1.0, @MatchScore) >= @MatchScore
 
GO

/****** Object:  StoredProcedure [sJRTCA].[spFuzzyMatch_Sire]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



 
--Use this code to execute the procedure once you've created it: EXEC [TestDB].[dbo].[FuzzyMatch_Company] @MatchScore = .8
 
CREATE procedure [sJRTCA].[spFuzzyMatch_Sire] (
 
@MatchScore float = .8 --You can change this every time you execute the stored procedure, but here I've set it to default to an 80% match or greater
,@DogName varchar(255)
 
) AS
 
TRUNCATE TABLE [sJRTCA].[Sire_TempMatch]
INSERT INTO [sJRTCA].[Sire_TempMatch]
 
SELECT ListA.SireID AS SireID
    ,ListA.Sire AS Sire
    ,ListB.DogID AS DogID
    ,ListB.DogName AS DogName
    ,MDS.mdq.Similarity(ListA.Sire, ListB.DogName,  0, 1.0, @MatchScore) as MatchScore
 
FROM (
    SELECT [SireID]
          ,[Sire]
    FROM [sAll].[Dog] d
	WHERE (@DogName IS NULL OR Sire LIKE '%' + @DogName + '%')
) ListA
 
JOIN (
    SELECT d.[DogID]
          ,d.[DogName]
    FROM [sAll].[Dog] d
    LEFT JOIN [sJRTCA].[Sire_FinalMatch] fin ON d.DogName = fin.DogName
    WHERE fin.SireID IS NULL
	AND (@DogName IS NULL OR fin.DogName LIKE '%' + @DogName + '%')
) ListB
 
ON MDS.mdq.Similarity(ListA.Sire, ListB.DogName, 0, 1.0, @MatchScore) >= @MatchScore
WHERE ListA.Sire IS NOT NULL
GO

/****** Object:  StoredProcedure [sJRTCA].[spInsertTrialPlacement]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [sJRTCA].[spInsertTrialPlacement] (@Result VARCHAR(2000),@TrialListID INT,@TrialClassID INT)
AS

DECLARE @Place VARCHAR(255)
DECLARE @Dog VARCHAR(255)
DECLARE @Owner VARCHAR(255)
DECLARE @OwnerID INT
DECLARE @DogID INT

SELECT @Place=@Result
SELECT @Dog=REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Place,CHARINDEX(':',@Place,1)+1,LEN(@Place)))),'†† ',''),'† ','')
SELECT @Owner=CASE WHEN @Dog LIKE '%owned by%' THEN
	REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,CHARINDEX('owned by ',@Dog,1)+LEN('owned by '),LEN(@Dog)))),'†† ',''),'† ','')
	ELSE '' END
SELECT @Dog=CASE WHEN @Dog LIKE '%owned by%' THEN
	REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,1,CHARINDEX('owned by',@Dog,1)-1))),'†† ',''),'† ','')
	ELSE @Dog END
SELECT @Dog=CASE WHEN @Dog LIKE '%,' THEN SUBSTRING(@Dog,1,LEN(@Dog)-1) ELSE @Dog END
SELECT @Place=RTRIM(SUBSTRING(@Place,1,CHARINDEX(':',@Place,1)-1))

IF NOT EXISTS (SELECT OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner)))
	INSERT sAll.Owner (OwnerName)
	SELECT LTRIM(RTRIM(@Owner))

SELECT @OwnerID=OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner))

IF NOT EXISTS (SELECT DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog)))
	INSERT sAll.Dog (OwnerID,DogName)
	SELECT @OwnerID, LTRIM(RTRIM(@Dog))

SELECT @DogID=DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog))

IF NOT EXISTS (SELECT TrialPlacementsID FROM sJRTCA.TrialPlacements WHERE TrialListID=@TrialListID AND TrialClassID=@TrialClassID AND DogID=@DogID)
	INSERT sJRTCA.TrialPlacements (TrialListID,TrialClassID,DogID,Result)
	SELECT @TrialListID,@TrialClassID,@DogID,@Place

SELECT @Dog,@DogID,@Owner,@OwnerID,@Place,@@IDENTITY
SELECT * FROM sjrtca.trialplacements where trialclassid=@TrialClassID
GO

/****** Object:  StoredProcedure [sJRTCA].[spLoadResults]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [sJRTCA].[spLoadResults] (@Year INT=NULL,@TrialName VARCHAR(100)=NULL,@StartDate DATE=NULL,@EndDate DATE=NULL,@JRTCA BIT=NULL,@TextFile VARCHAR(255)=NULL,@TrialListID INT=NULL) AS

IF @TrialListID IS NULL
BEGIN
	INSERT sJRTCA.TrialList ([Year],TrialName,StartDate,EndDate,TrialResultFilePath,JRTCA)
	SELECT @Year,@TrialName,@StartDate,@EndDate,@TextFile,@JRTCA
	
	SELECT @TrialListID=@@IDENTITY
END

IF @TextFile IS NOT NULL
BEGIN
	DECLARE @SQL NVARCHAR(MAX)

	SELECT @SQL = '
		SELECT 
			' + CAST(@TrialListID AS VARCHAR(10)) + ',*
		FROM OPENROWSET(BULK N''' + @TextFile + ''', SINGLE_CLOB) AS Contents
	'

	INSERT sJRTCA.RawTrialResults (TrialListID,Results)
	EXEC (@SQL)

	PRINT @SQL
END

EXEC t.sJRTCA.spParseRawResults @TrialListID
EXEC t.sJRTCA.spParseTrialResults @TrialListID

select 'Chair/Location',Chairperson,LocationCity,LocationState FROM t.sjrtca.triallist where triallistid=@TrialListID
UNION ALL
select 'Conf Judge',JudgeName,NULL,NULL FROM t.sjrtca.triallist_judges where triallistid=@TrialListID AND DivisionID=(SELECT divisionID from t.sjrtca.Division where DivisionName='CONFORMATION')
UNION ALL
select 'GTG Judge',JudgeName,NULL,NULL FROM t.sjrtca.triallist_judges where triallistid=@TrialListID AND DivisionID=(SELECT divisionID from t.sjrtca.Division where DivisionName='GO-TO-GROUND')

select distinct result from t.sjrtca.TrialPlacements where TrialListID=@TrialListID and result not in ('1st','2nd','3rd','4th','5th','6th','best','champion','reserve')
select d.DivisionName,c.ClassName,s.ClassCount from t.sjrtca.class c join t.sjrtca.division d on c.divisionid=d.divisionid join (select c.classid,count(1) AS ClassCount from t.sjrtca.class c join t.sjrtca.trialclass tc on c.classid=tc.classid group by c.classid) s on c.classid=s.classid where c.classid in (
select classid from t.sjrtca.trialclass where TrialListID=@TrialListID) and s.ClassCount<=25 order by c.classname
select d.DivisionName,s.DivisionCount from t.sjrtca.division d join (select d.divisionid,count(1) DivisionCount from t.sjrtca.division d join t.sjrtca.class c on d.divisionid=c.divisionid join t.sjrtca.trialclass tc on c.classid=tc.classid group by d.divisionid) s on d.divisionid=s.divisionid where s.DivisionCount<=50

update t.sjrtca.triallist set loaded=1 where triallistid in (@TrialListID)
GO

/****** Object:  StoredProcedure [sJRTCA].[spLookupClassNameIssues]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [sJRTCA].[spLookupClassNameIssues] AS

select tc.trialclassid,c.*,tl.*
from t.sjrtca.class c
join t.sjrtca.trialclass tc on c.classid=tc.classid
join t.sjrtca.triallist tl on tc.triallistid=tl.triallistid
where c.classname like '%:%' and c.classname not like 'class%'
and c.classid in (
	select c.classid
	from t.sjrtca.trialclass tc
	join t.sjrtca.class c on tc.classid=c.classid
	join t.sjrtca.division d on c.divisionid=d.divisionid
	group by c.classid
	having count(tc.classid)=1
)
order by c.classname
GO

/****** Object:  StoredProcedure [sJRTCA].[spOwnerCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



CREATE PROCEDURE [sJRTCA].[spOwnerCleanup] (@MatchScore FLOAT=.9,@OwnerName varchar(255)=NULL,@Year INT=NULL,@OwnerCount INT=500) AS
	EXEC [sJRTCA].[spFuzzyMatch_Owner] @MatchScore,@OwnerName,@Year

	; WITH MinMatch AS (
		SELECT DISTINCT 
			m.FirstOwnerID,m.FirstOwnerName,Min(m.MatchScore) OVER (PARTITION BY FirstOwnerID,FirstOwnerName) AS MatchScore,COUNT(*) OVER (PARTITION BY m.firstownerid) AS OwnerCount
		FROM sJRTCA.Owner_TempMatch m
		JOIN sall.dog d on m.firstownerid=d.ownerid
		JOIN sJRTCA.trialplacements tp on d.dogid=tp.dogid
		where firstOwnerid<>secondOwnerid
	)
	SELECT DISTINCT 
		'UPDATE ' + DB_NAME() + '.sall.dog SET OwnerID=' + CAST(m.FirstOwnerID AS VARCHAR(25)) + ' WHERE OwnerID=' + CAST(t.SecondOwnerID AS VARCHAR(25)) + '--' + m.FirstOwnerName + ' from ' + t.SecondOwnerName,m.FirstOwnerID,m.FirstOwnerName,t.SecondOwnerID,t.SecondOwnerName,m.MatchScore,m.OwnerCount,ROW_NUMBER() OVER (ORDER BY m.OwnerCount DESC) AS RowNumber
	FROM MinMatch m
	JOIN sJRTCA.Owner_TempMatch t ON m.FirstOwnerID=t.FirstOwnerID AND m.MatchScore=t.MatchScore
	where t.firstOwnerid<>t.secondOwnerid 
	and ((t.firstownername not like '%/%' and t.secondownername not like '%/%' and t.firstownername not like '%&%' and t.secondownername not like '%&%') or (t.firstownername like '%&%' and t.secondownername like '%&%') or (t.firstownername like '%/%' and t.secondownername like '%/%') or (t.firstownername like '%/%' and t.secondownername like '%&%') or (t.firstownername like '%&%' and t.secondownername like '%/%'))
	and m.ownercount>=@OwnerCount
	UNION
	SELECT TOP 1
		'delete ' + DB_NAME() + '.sall.owner where ownerid not in (select distinct ownerid from ' + DB_NAME() + '.sall.dog) and ownerid not in (1);',NULL,NULL,NULL,NULL,NULL,NULL,999999 AS RowNumber
	order by m.FirstOwnerName,m.OwnerCount DESC;
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseEntries]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseEntries] (@TrialListID INT) AS

DECLARE @EntryID INT
DECLARE @Count INT
DECLARE @InnerResultID INT
DECLARE @InnerCount INT
DECLARE @Entry VARCHAR(2000)
DECLARE @NextEntry VARCHAR(2000)
DECLARE @Division VARCHAR(255)
DECLARE @DogNumber VARCHAR(255)
DECLARE @Class VARCHAR(255)
DECLARE @EntryCount VARCHAR(100)
DECLARE @Dog VARCHAR(255)
DECLARE @Sire VARCHAR(255)
DECLARE @Dam VARCHAR(255)
DECLARE @Owner VARCHAR(255)

DECLARE @DivisionID INT
DECLARE @ClassID INT
DECLARE @TrialClassID INT
DECLARE @OwnerID INT
DECLARE @DogID INT

SELECT @EntryID=MIN(TrialEntriesID)
FROM sJRTCA.TrialEntries
WHERE TrialListID=@TrialListID
SELECT @Count=MAX(TrialEntriesID)
FROM sJRTCA.TrialEntries
WHERE TrialListID=@TrialListID

PRINT 'TrialListID: ' + CAST(@TrialListID AS VARCHAR(10))

WHILE @EntryID<=@Count
BEGIN
	SELECT @Entry=LTRIM(RTRIM(Entries))
	FROM sJRTCA.TrialEntries
	WHERE TrialEntriesID=@EntryID

	PRINT 'Line: ' + @Entry + '; Count: ' + CAST(@EntryID AS VARCHAR(100))

	IF RTRIM(LTRIM(@Entry)) in 
		('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
		'BALL RETRIEVAL',
		'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
		'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
		'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
		'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
		'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
		'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
		'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
		'GAMES CLASSES',
		'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
		'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
		'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
		'JUMPERS DIVISION',
		'NON-SANCTIONED DIVISION',
		'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
		'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
		'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
		'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
		'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
		'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
		'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
		'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
		'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
		'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
		'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
	BEGIN
		PRINT 'Outer champ/division check: ' + @Entry

		SELECT @Division=@Entry

		SELECT @Division = CASE
			WHEN LTRIM(RTRIM(@Division)) IN ('AGILILITY','AGILITY DIVISION','AGILITY DIVISON','AGILITY') THEN 'AGILITY DIVISION'
			WHEN LTRIM(RTRIM(@Division)) IN ('BALL RETRIEVAL') THEN 'BALL RETRIEVAL'
			WHEN LTRIM(RTRIM(@Division)) IN ('BALL TOSS') THEN 'BALL TOSS'
			WHEN LTRIM(RTRIM(@Division)) IN ('BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION') THEN 'BARN HUNT'
			WHEN LTRIM(RTRIM(@Division)) IN ('BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)') THEN 'BRUSH HUNT'
			WHEN LTRIM(RTRIM(@Division)) IN ('BRUSH HUNT: SATURDAY') THEN 'BRUSH HUNT: SATURDAY'
			WHEN LTRIM(RTRIM(@Division)) IN ('BRUSH HUNT: SUNDAY') THEN 'BRUSH HUNT: SUNDAY'
			WHEN LTRIM(RTRIM(@Division)) IN ('CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††') THEN 'CONFORMATION'
			WHEN LTRIM(RTRIM(@Division)) IN ('DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION') THEN 'DOGGIE FUN ZONE (Non-sanctioned)'
			WHEN LTRIM(RTRIM(@Division)) IN ('LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)') THEN 'LURE COURSING'
			WHEN LTRIM(RTRIM(@Division)) IN ('FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS') THEN 'FLAT RACES'
			WHEN LTRIM(RTRIM(@Division)) IN ('GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG') THEN 'GO-TO-GROUND'
			WHEN LTRIM(RTRIM(@Division)) IN ('HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE') THEN 'HIGH JUMP'
			WHEN LTRIM(RTRIM(@Division)) IN ('HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races','STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES') THEN 'STEEPLECHASE RACES'
			WHEN LTRIM(RTRIM(@Division)) IN ('JUMPERS DIVISION') THEN 'JUMPERS DIVISION'
			WHEN LTRIM(RTRIM(@Division)) IN ('OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE') THEN 'OBEDIENCE DIVISION'
			WHEN LTRIM(RTRIM(@Division)) IN ('RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE') THEN 'RALLY OBEDIENCE DIVISION'
			WHEN LTRIM(RTRIM(@Division)) IN ('SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION') THEN 'SUPER EARTH'
			WHEN LTRIM(RTRIM(@Division)) IN ('THUNDER TUNNEL','THUNDER TUNNEL DIVISION') THEN 'THUNDER TUNNEL'
			WHEN LTRIM(RTRIM(@Division)) IN ('TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION') THEN 'TRAILING & LOCATING'
			WHEN LTRIM(RTRIM(@Division)) IN ('TOP DOG') THEN 'TOP DOG'
			WHEN LTRIM(RTRIM(@Division)) IN ('TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)') THEN 'TOP GUN'
			WHEN LTRIM(RTRIM(@Division)) IN ('YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT','YOUTH') THEN 'YOUTH DIVISION'
			ELSE 'UNKNOWN DIVISION!' END

		----display division information
		PRINT 'Division: ' + @Division
		SELECT @InnerResultID=@EntryID+1,@InnerCount=@Count

		WHILE @InnerResultID<=@InnerCount
		BEGIN
			IF ISNULL(@NextEntry,'')<>''
			BEGIN
				SELECT @InnerResultID-=1
				SELECT @Entry=@NextEntry
				SELECT @NextEntry=NULL
			END
			ELSE
			BEGIN
				SELECT @Entry=NULL
				SELECT @NextEntry=NULL

				SELECT @Entry=REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(Entries)),'|',''),'|',''),' ',' '),' :  ',': '),'†',' '),'††††††',' '),'†††††††',' '),'†††††† ',' '),'† ',' ')
				FROM sJRTCA.TrialEntries
				WHERE TrialEntriesID=@InnerResultID
			END

			IF ISNULL(@Entry,'')<>'' AND @Entry NOT in 
				('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
				'BALL RETRIEVAL',
				'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
				'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
				'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
				'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
				'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
				'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
				'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
				'GAMES CLASSES',
				'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
				'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
				'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
				'JUMPERS DIVISION',
				'NON-SANCTIONED DIVISION',
				'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
				'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
				'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
				'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
				'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
				'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
				'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
				'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
				'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
				'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
				'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				IF @Entry LIKE 'Class: %' OR @Entry IN (SELECT DISTINCT ClassName FROM sJRTCA.Class)
				BEGIN
					SELECT @Class=CASE
						WHEN RTRIM(@Entry) LIKE 'Class: %' THEN LTRIM(RTRIM(REPLACE(@Entry,'Class: ','')))
						WHEN RTRIM(@Entry) IN (SELECT DISTINCT ClassName FROM sJRTCA.Class) THEN LTRIM(RTRIM(@Entry))
						ELSE RTRIM(@Entry) END
				END
				ELSE IF @Entry NOT LIKE 'Class%'
				BEGIN
					SELECT @DogNumber=LTRIM(RTRIM(SUBSTRING(@Entry,1,CHARINDEX(' ',@Entry,1)-1)))
					SELECT @Dog=CASE
						WHEN @Entry LIKE '%, by %' THEN LTRIM(RTRIM(SUBSTRING(@Entry,CHARINDEX(' ',@Entry,1)+LEN(' '),CHARINDEX(', by ',@Entry,1)-CHARINDEX(' ',@Entry,1)+LEN(' '))))
						WHEN @Entry NOT LIKE '%, by %' AND @Entry LIKE '% (%' THEN LTRIM(RTRIM(SUBSTRING(@Entry,CHARINDEX(' ',@Entry,1)+1,CHARINDEX(' (',@Entry,1)-CHARINDEX(' ',@Entry,1)+1-LEN(' ('))))
						ELSE NULL END

					SELECT @Sire=CASE
						WHEN @Entry LIKE '%, by %' AND @Entry LIKE '% out of %' THEN LTRIM(RTRIM(SUBSTRING(@Entry,CHARINDEX(', by ',@Entry,1)+LEN(', by '),CHARINDEX(' out of ',@Entry,1)-CHARINDEX(', by ',@Entry,1)+LEN(', by ')-LEN(' out of '))))
						WHEN @Entry LIKE '%, by %' AND @Entry NOT LIKE '% out of %' THEN LTRIM(RTRIM(SUBSTRING(@Entry,CHARINDEX(', by ',@Entry,1)+LEN(', by '),CHARINDEX(' (',@Entry,1)-CHARINDEX(', by ',@Entry,1)-1-LEN(' ('))))
						ELSE '' END

					SELECT @Dam=CASE
						WHEN @Entry LIKE '% out of %' THEN LTRIM(RTRIM(SUBSTRING(@Entry,CHARINDEX(' out of ',@Entry,1)+LEN(' out of '),CHARINDEX(' (',@Entry,1)-CHARINDEX(' out of ',@Entry,1)-LEN(' out of '))))
						ELSE '' END

					SELECT @Owner=CASE
						WHEN @Entry LIKE '% (%' THEN LTRIM(RTRIM(SUBSTRING(@Entry,CHARINDEX(' (',@Entry,1)+LEN(' ('),CHARINDEX(')',@Entry,1)-CHARINDEX(' (',@Entry,1)-LEN(' ('))))
						ELSE '' END

					-- display all individual results
					PRINT @InnerResultID
					PRINT 'Division: ' + @Division
					--PRINT CASE WHEN ISNULL(@Championship,'')<>'' THEN 'Champ: ' + ISNULL(@Championship,'') ELSE '' END
					PRINT 'Class: ' + ISNULL(@Class,'')
					PRINT 'DogNumber: ' + ISNULL(@DogNumber,'')
					PRINT 'Dog: ' + ISNULL(@Dog,'')
					PRINT 'Sire: ' + ISNULL(@Sire,'')
					PRINT 'Dam: ' + ISNULL(@Dam,'')
					PRINT 'Owner: ' + ISNULL(@Owner,'')
					PRINT ''

					IF NOT EXISTS (SELECT OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner)))
						INSERT sAll.Owner (OwnerName)
						SELECT LTRIM(RTRIM(@Owner))

					SELECT @OwnerID=OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner))

					IF NOT EXISTS (SELECT DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog)))
						INSERT sAll.Dog (OwnerID,DogName,Sire,Dam)
						SELECT @OwnerID, LTRIM(RTRIM(@Dog)),LTRIM(RTRIM(@Sire)),LTRIM(RTRIM(@Dam))
					ELSE IF NOT EXISTS (SELECT DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog)) AND (Sire=LTRIM(RTRIM(@Sire)) OR Dam=LTRIM(RTRIM(@Dam))))
						UPDATE sAll.Dog
						SET Sire=LTRIM(RTRIM(@Sire)),Dam=LTRIM(RTRIM(@Dam))
						WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog))

					SELECT @DogID=DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog))

					SELECT @TrialClassID=tc.TrialClassID
					FROM sJRTCA.TrialClass tc
					JOIN sJRTCA.TrialList tl ON tc.TrialListID=tl.TrialListID
					JOIN sJRTCA.Class c ON tc.ClassID=c.ClassID
					JOIN sJRTCA.Division d ON c.DivisionID=d.DivisionID
					WHERE tl.TrialListID=@TrialListID AND c.ClassName=@Class AND d.DivisionName=@Division

					IF NOT EXISTS (SELECT DogID FROM sJRTCA.DogTrialEntries WHERE TrialListID=@TrialListID AND TrialClassID=@TrialClassID AND DogID=@DogID)
						INSERT sJRTCA.DogTrialEntries (TrialListID,TrialClassID,DogID)
						SELECT @TrialListID,@TrialClassID,@DogID
				END

				SELECT @InnerResultID+=1
			END
			ELSE IF ISNULL(@Entry,'')<>'' AND RTRIM(LTRIM(@Entry)) IN 
				('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
				'BALL RETRIEVAL',
				'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
				'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
				'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
				'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
				'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
				'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
				'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
				'GAMES CLASSES',
				'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
				'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
				'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
				'JUMPERS DIVISION',
				'NON-SANCTIONED DIVISION',
				'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
				'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
				'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
				'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
				'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
				'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
				'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
				'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
				'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
				'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
				'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				SELECT @InnerCount=@InnerResultID-2
				SELECT @InnerResultID-=1
			END
			ELSE IF ISNULL(@Entry,'')=''
				SELECT @InnerResultID+=1
		END
	END

	IF ISNULL(@InnerResultID,0)<>0
		SELECT @EntryID=@InnerResultID

	SELECT @EntryID+=1
END
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseEntriesClasses]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseEntriesClasses] (@TrialListID INT,@TextFile VARCHAR(255)=NULL,@PrintOutput BIT=0) AS

DECLARE @SQL NVARCHAR(MAX)

IF @TextFile IS NOT NULL
BEGIN
	SELECT @SQL = '
		SELECT 
			' + CAST(@TrialListID AS VARCHAR(10)) + ',*
		FROM OPENROWSET(BULK N''' + @TextFile + ''', SINGLE_CLOB) AS Contents
	'

	INSERT sJRTCA.RawTrialEntriesClasses (TrialListID,Classes)
	EXEC (@SQL)

	PRINT @SQL
END

DECLARE @text NVARCHAR(MAX), @text1 NVARCHAR(MAX)

SELECT 
	@text=SUBSTRING(Classes,1,CHARINDEX('FLAT RACES',Classes,1)),
	@text1=SUBSTRING(Classes,CHARINDEX('FLAT RACES',Classes,1),LEN(Classes)) + char(13) + char(10) + 'end of text'
FROM sJRTCA.RawTrialEntriesClasses
WHERE TrialListID=@TrialListID

select @text,@text1

DECLARE @Delimiter VARCHAR(1000)= CHAR(13) + CHAR(10)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialEntriesClasses (TrialListID,Classes)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
FROM res
OPTION (MAXRECURSION 0)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text1, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text1, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text1, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialEntriesClasses (TrialListID,Classes)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
FROM res
OPTION (MAXRECURSION 0)

IF ISNULL(@PrintOutput,0)=1
	SELECT * FROM sJRTCA.TrialEntriesClasses WHERE TrialListID=@TrialListID

DECLARE @EntryID INT
DECLARE @Count INT
DECLARE @InnerResultID INT
DECLARE @InnerCount INT
DECLARE @Entry VARCHAR(2000)
DECLARE @NextEntry VARCHAR(2000)
DECLARE @Division VARCHAR(255)
DECLARE @DogNumber VARCHAR(255)
DECLARE @Class VARCHAR(255)
DECLARE @EntryCount VARCHAR(100)
DECLARE @Dog VARCHAR(255)
DECLARE @Sire VARCHAR(255)
DECLARE @Dam VARCHAR(255)
DECLARE @Owner VARCHAR(255)

DECLARE @DivisionID INT
DECLARE @ClassID INT
DECLARE @TrialClassID INT
DECLARE @OwnerID INT
DECLARE @DogID INT

SELECT @EntryID=MIN(TrialEntriesClassesID)
FROM sJRTCA.TrialEntriesClasses
WHERE TrialListID=@TrialListID
SELECT @Count=MAX(TrialEntriesClassesID)
FROM sJRTCA.TrialEntriesClasses
WHERE TrialListID=@TrialListID

PRINT 'TrialListID: ' + CAST(@TrialListID AS VARCHAR(10))

WHILE @EntryID<=@Count
BEGIN
	SELECT @Entry=LTRIM(RTRIM(Classes))
	FROM sJRTCA.TrialEntriesClasses
	WHERE TrialEntriesClassesID=@EntryID

	PRINT 'Line: ' + @Entry + '; Count: ' + CAST(@EntryID AS VARCHAR(100))

	IF RTRIM(LTRIM(@Entry)) in 
		('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
		'BALL RETRIEVAL',
		'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
		'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
		'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
		'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
		'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
		'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
		'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
		'GAMES CLASSES',
		'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
		'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
		'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
		'JUMPERS DIVISION',
		'NON-SANCTIONED DIVISION',
		'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
		'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
		'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
		'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
		'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
		'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
		'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
		'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
		'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
		'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
		'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
	BEGIN
		PRINT 'Outer champ/division check: ' + @Entry

		SELECT @Division=@Entry

		SELECT @Division = CASE
			WHEN @Division IN ('AGILILITY','AGILITY DIVISION','AGILITY DIVISON','AGILITY') THEN 'AGILITY DIVISION'
			WHEN @Division IN ('BALL RETRIEVAL') THEN 'BALL RETRIEVAL'
			WHEN @Division IN ('BALL TOSS') THEN 'BALL TOSS'
			WHEN @Division IN ('BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION') THEN 'BARN HUNT'
			WHEN @Division IN ('BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)') THEN 'BRUSH HUNT'
			WHEN @Division IN ('BRUSH HUNT: SATURDAY') THEN 'BRUSH HUNT: SATURDAY'
			WHEN @Division IN ('BRUSH HUNT: SUNDAY') THEN 'BRUSH HUNT: SUNDAY'
			WHEN @Division IN ('CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††') THEN 'CONFORMATION'
			WHEN @Division IN ('DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION') THEN 'DOGGIE FUN ZONE (Non-sanctioned)'
			WHEN @Division IN ('LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)') THEN 'LURE COURSING'
			WHEN @Division IN ('FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS') THEN 'FLAT RACES'
			WHEN @Division IN ('GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG') THEN 'GO-TO-GROUND'
			WHEN @Division IN ('HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE') THEN 'HIGH JUMP'
			WHEN @Division IN ('HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races','STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES') THEN 'STEEPLECHASE RACES'
			WHEN @Division IN ('JUMPERS DIVISION') THEN 'JUMPERS DIVISION'
			WHEN @Division IN ('OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE') THEN 'OBEDIENCE DIVISION'
			WHEN @Division IN ('RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE') THEN 'RALLY OBEDIENCE DIVISION'
			WHEN @Division IN ('SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION') THEN 'SUPER EARTH'
			WHEN @Division IN ('THUNDER TUNNEL','THUNDER TUNNEL DIVISION') THEN 'THUNDER TUNNEL'
			WHEN @Division IN ('TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION') THEN 'TRAILING & LOCATING'
			WHEN @Division IN ('TOP DOG') THEN 'TOP DOG'
			WHEN @Division IN ('TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)') THEN 'TOP GUN'
			WHEN @Division IN ('YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT','YOUTH') THEN 'YOUTH DIVISION'
			ELSE 'UNKNOWN DIVISION!' END

		----display division information
		PRINT 'Division: ' + @Division
		SELECT @InnerResultID=@EntryID+1,@InnerCount=@Count

		WHILE @InnerResultID<=@InnerCount
		BEGIN
			IF ISNULL(@NextEntry,'')<>''
			BEGIN
				SELECT @InnerResultID-=1
				SELECT @Entry=@NextEntry
				SELECT @NextEntry=NULL
			END
			ELSE
			BEGIN
				SELECT @Entry=NULL
				SELECT @NextEntry=NULL

				SELECT @Entry=REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(Classes)),'|',''),'|',''),' ',' '),' :  ',': '),'†',' '),'††††††',' '),'†††††††',' '),'†††††† ',' '),'† ',' ')
				FROM sJRTCA.TrialEntriesClasses
				WHERE TrialEntriesClassesID=@InnerResultID
			END

			IF ISNULL(@Entry,'')<>'' AND @Entry NOT in 
				('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
				'BALL RETRIEVAL',
				'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
				'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
				'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
				'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
				'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
				'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
				'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
				'GAMES CLASSES',
				'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
				'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
				'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
				'JUMPERS DIVISION',
				'NON-SANCTIONED DIVISION',
				'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
				'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
				'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
				'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
				'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
				'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
				'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
				'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
				'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
				'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
				'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				SELECT @Class=RTRIM(LTRIM(@Entry))

				SELECT @Class=replace(@Class,'¬','') where @Class like '%¬%'
				SELECT @Class=replace(@Class,'Ä','"') where @Class like '%Ä%'

				SELECT @TrialClassID=tc.TrialClassID
				FROM sJRTCA.TrialClass tc
				JOIN sJRTCA.TrialList tl ON tc.TrialListID=tl.TrialListID
				JOIN sJRTCA.Class c ON tc.ClassID=c.ClassID
				JOIN sJRTCA.Division d ON c.DivisionID=d.DivisionID
				WHERE tl.TrialListID=@TrialListID AND c.ClassName=@Class AND d.DivisionName=@Division

				IF @TrialClassID IS NULL
				BEGIN
					INSERT sJRTCA.Class (DivisionID,ClassName)
					SELECT DivisionID,@Class
					FROM sJRTCA.Division
					WHERE DivisionName=@Division

					SELECT @ClassID=@@IDENTITY

					INSERT sJRTCA.TrialClass (TrialListID,ClassID,EntriesOnly)
					SELECT @TrialListID,@ClassID,1
				END

				SELECT @InnerResultID+=1
			END
			ELSE IF ISNULL(@Entry,'')<>'' AND RTRIM(LTRIM(@Entry)) IN 
				('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
				'BALL RETRIEVAL',
				'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
				'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
				'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
				'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
				'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
				'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
				'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
				'GAMES CLASSES',
				'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
				'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
				'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
				'JUMPERS DIVISION',
				'NON-SANCTIONED DIVISION',
				'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
				'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
				'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
				'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
				'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
				'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
				'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
				'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
				'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
				'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
				'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				SELECT @InnerCount=@InnerResultID-2
				SELECT @InnerResultID-=1
			END
			ELSE IF ISNULL(@Entry,'')=''
				SELECT @InnerResultID+=1
		END
	END

	IF ISNULL(@InnerResultID,0)<>0
		SELECT @EntryID=@InnerResultID

	SELECT @EntryID+=1
END
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseRawEntries]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseRawEntries] (@TrialListID INT,@TextFile VARCHAR(255)=NULL,@PrintOutput BIT=0) AS

DECLARE @SQL NVARCHAR(MAX)

IF @TextFile IS NOT NULL
BEGIN
	SELECT @SQL = '
		SELECT 
			' + CAST(@TrialListID AS VARCHAR(10)) + ',*
		FROM OPENROWSET(BULK N''' + @TextFile + ''', SINGLE_CLOB) AS Contents
	'

	INSERT sJRTCA.RawTrialEntries (TrialListID,Entries)
	EXEC (@SQL)

	PRINT @SQL
END

DECLARE @text NVARCHAR(MAX), @text1 NVARCHAR(MAX), @text2 NVARCHAR(MAX), @text3 NVARCHAR(MAX)

SELECT 
	LEN(Entries) as LenEntries
FROM sJRTCA.RawTrialEntries
WHERE TrialListID=@TrialListID

SELECT 
	@text=SUBSTRING(Entries,1,CHARINDEX('FLAT RACES',Entries,1)),
	@text1=SUBSTRING(Entries,CHARINDEX('FLAT RACES',Entries,1),CASE WHEN LEN(Entries)>75000 THEN 75000 ELSE LEN(Entries) END) + CASE WHEN LEN(Entries)>75000 THEN  + char(13) + char(10) + 'end of text' ELSE '' END,
	@text2=CASE
		WHEN LEN(Entries)>150000 THEN SUBSTRING(Entries,75001,150000)
		WHEN LEN(Entries) BETWEEN 75000 AND 150000 THEN SUBSTRING(Entries,75001,LEN(Entries)) + char(13) + char(10) + 'end of text'
		ELSE '' END,
	@text3=SUBSTRING(Entries,150001,LEN(Entries)) + char(13) + char(10) + 'end of text'
FROM sJRTCA.RawTrialEntries
WHERE TrialListID=@TrialListID

select @text,@text1,@text2,@text3,len(@text),len(@text1),len(@text2),len(@text3)

DECLARE @Delimiter NVARCHAR(MAX)= CHAR(13) + CHAR(10)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialEntries (TrialListID,Entries)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
FROM res
OPTION (MAXRECURSION 0)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text1, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text1, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text1, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialEntries (TrialListID,Entries)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
FROM res
OPTION (MAXRECURSION 0)

IF ISNULL(@text2,'')<>''
	WITH numbers AS (
		SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
		FROM sys.objects o
		CROSS JOIN sys.objects o2
	), c AS (
		SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
		FROM numbers
		WHERE SUBSTRING(@text2, Number, LEN(@Delimiter)) = @Delimiter
	), res AS (
		SELECT CHARBegin, CAST(LEFT(@text2, charbegin) AS NVARCHAR(MAX)) AS Res, RN
		FROM c
		WHERE rn = 1
		UNION ALL
		SELECT c.CHARBegin, CAST(SUBSTRING(@text2, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
		FROM	c
		JOIN res ON c.RN = res.RN + 1
	) 
	INSERT sJRTCA.TrialEntries (TrialListID,Entries)
	SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
	FROM res
	OPTION (MAXRECURSION 0)

IF ISNULL(@text3,'')<>''
	WITH numbers AS (
		SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
		FROM sys.objects o
		CROSS JOIN sys.objects o2
	), c AS (
		SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
		FROM numbers
		WHERE SUBSTRING(@text3, Number, LEN(@Delimiter)) = @Delimiter
	), res AS (
		SELECT CHARBegin, CAST(LEFT(@text3, charbegin) AS NVARCHAR(MAX)) AS Res, RN
		FROM c
		WHERE rn = 1
		UNION ALL
		SELECT c.CHARBegin, CAST(SUBSTRING(@text3, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
		FROM	c
		JOIN res ON c.RN = res.RN + 1
	) 
	INSERT sJRTCA.TrialEntries (TrialListID,Entries)
	SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
	FROM res
	OPTION (MAXRECURSION 0)

IF ISNULL(@PrintOutput,0)=1
	SELECT * FROM sJRTCA.TrialEntries WHERE TrialListID=@TrialListID
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseRawResults]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseRawResults] (@TrialListID INT,@PrintOutput BIT=0) AS

IF object_id('tempdb..#tmpResults') IS NOT NULL
	DROP TABLE #tmpResults

DECLARE @text NVARCHAR(MAX), @text1 NVARCHAR(MAX)

SELECT 
	@text=SUBSTRING(Results,1,CHARINDEX('RACING DIVISION',Results,1)),
	@text1=SUBSTRING(results,CHARINDEX('RACING DIVISION',Results,1),LEN(results)) + char(13) + char(10) + 'end of text'
FROM sJRTCA.RawTrialResults
WHERE TrialListID=@TrialListID

CREATE TABLE #tmpResults
	(Results NVARCHAR(MAX))

DECLARE @Delimiter VARCHAR(1000)= CHAR(13) + CHAR(10)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialResults (TrialListID,Results)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
FROM res
OPTION (MAXRECURSION 0)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text1, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text1, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text1, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialResults (TrialListID,Results)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
FROM res
OPTION (MAXRECURSION 0)

IF ISNULL(@PrintOutput,0)=1
	SELECT * FROM sJRTCA.TrialResults WHERE TrialListID=@TrialListID
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseRawResultsFromText]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseRawResultsFromText] (@TrialListID INT,@TextFile VARCHAR(255)) AS

IF object_id('tempdb..#tmpBulkResults') IS NOT NULL
	DROP TABLE #tmpBulkResults
IF object_id('tempdb..#tmpResults') IS NOT NULL
	DROP TABLE #tmpResults

DECLARE @text NVARCHAR(MAX), @text1 NVARCHAR(MAX)
DECLARE @SQL NVARCHAR(MAX)
DECLARE @Year INT

CREATE TABLE #tmpBulkResults
	([text] NVARCHAR(MAX))

SELECT @SQL = '
	SELECT 
		*
	FROM OPENROWSET(BULK N''' + @TextFile + ''', SINGLE_CLOB) AS Contents
'

INSERT #tmpBulkResults
EXEC (@SQL)

PRINT @SQL

UPDATE #tmpBulkResults SET [text]=REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
		[text],'¬',''),'Ä','"'),'‚Äô',''''),'"ô',''''),'"ì','ñ'),'  ',' '),' †',' '),'††',' '),'  ',' '),'VETERANS, RACING †CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE'),'†',''),'Reserve Champion: ','Reserve: '),'High Point Champion: ','Champion: '),'High Score: ','Champion: '),'Reserve Best: ','Reserve: '),'1st ','1st:'),'2nd ','2nd:'),'3rd ','3rd:'),'4th ','4th:'),'5th ','5th:'),'6th ','6th:'),' tie:',':'),'1 st:','1st:'),'Entries : ','Entries: ')
		,'12Y2 up to 15"','12Ω up to 15"'),'10 up to 12Y2"','10 up to 12Ω"'),'10 up to 12W''','10 up to 12Ω"'),'12% up to 15"','12Ω up to 15"'),'12Y2 -15"','12Ω up to 15"'),'12Y2-1S"','12Ω up to 15"'),'10 up to 12%','10 up to 12Ω'),'12112-15"','12Ω up to 15"'),'10 up to 12112"','10 up to 12Ω"'),'10" to 12W''','10 up to 12Ω"'),'12W'' to 15"','12Ω up to 15"'),'121/2-15"','12Ω up to 15"'),'10-12%"','10 up to 12Ω"'),'10-12Y2"','10 up to 12Ω"'),'12Y2- 15"','12Ω up to 15"')
		,'0-12112"','10 up to 12Ω"'),'rlbr','r/br'),'12•z-15"','12Ω up to 15"'),'12Yz-15"','12Ω up to 15"'),'10" up to 12Y2"','10 up to 12Ω"'),'over 12Y2-15"','12Ω up to 15"'),'over 12% .. 15"','12Ω up to 15"'),'121/2"15"','12Ω up to 15"'),'12V2" 15"','12Ω up to 15"'),'12% .. 15"','12Ω up to 15"'),'10-12112"','10 up to 12Ω"'),'12V2-15"','12Ω up to 15"'),'10-12W''','10 up to 12Ω"'),'110 up to 12Ω"','10 up to 12Ω"'),'12V2"15"','12Ω up to 15"'),'12%-15"','12Ω up to 15"')
		,'12% "¢. 15"','12Ω up to 15"'),'12%∑15"','12Ω up to 15"'),'""','"'),'1()''12''12"','10 up to 12Ω"'),'12V2"15"','12Ω up to 15"'),'12''12∑15"','12Ω up to 15"'),'121/2∑15','12Ω up to 15'),'1()''121/2','10 up to 12Ω"'),'1()''12''/2','10 up to 12Ω"'),'10-121/2','10 up to 12Ω"'),'''/2''','12Ω'),'12 ''1,∑15','12Ω up to 15'),'12 ''/,∑15"','12Ω up to 15'),'12 %∑15"','12Ω up to 15'),'12 1/2','12Ω'),'10∑121/2"','10 up to 12Ω"'),'121/2∑15"','12Ω up to 15'),'10∑12112','10 up to 12Ω"')
		,' (1 entry)',' - Entries: 1')
		,' (2 entries)',' - Entries: 2')
		,' (3 entries)',' - Entries: 3')
		,' (4 entries)',' - Entries: 4')
		,' (5 entries)',' - Entries: 5')
		,' (6 entries)',' - Entries: 6')
		,' (7 entries)',' - Entries: 7')
		,' (8 entries)',' - Entries: 8')
		,' (9 entries)',' - Entries: 9')
		,' (10 entries)',' - Entries: 10')
		,' (11 entries)',' - Entries: 11')
		,' (12 entries)',' - Entries: 12')
		,' (13 entries)',' - Entries: 13')
		,' (14 entries)',' - Entries: 14')
		,' (15 entries)',' - Entries: 15')
		,' (16 entries)',' - Entries: 16')
		,' (17 entries)',' - Entries: 17')
		,' (18 entries)',' - Entries: 18')
		,' (19 entries)',' - Entries: 19')
		,' (20 entries)',' - Entries: 20')
		,' (21 entries)',' - Entries: 21')
		,' (22 entries)',' - Entries: 22')
		,' (23 entries)',' - Entries: 23')
		,' (24 entries)',' - Entries: 24')
		,' (25 entries)',' - Entries: 25')
		,' (26 entries)',' - Entries: 26')
		,' (27 entries)',' - Entries: 27')
		,' (28 entries)',' - Entries: 28')
		,' (29 entries)',' - Entries: 29')
		,' (30 entries)',' - Entries: 30')
		,' (31 entries)',' - Entries: 31')
		,' (32 entries)',' - Entries: 32')
		,' (33 entries)',' - Entries: 33')
		,' (34 entries)',' - Entries: 34')
		,' (35 entries)',' - Entries: 35')
		,' (36 entries)',' - Entries: 36')
		,' (37 entries)',' - Entries: 37')
		,' (38 entries)',' - Entries: 38')
		,' (39 entries)',' - Entries: 39')
		,' (40 entries)',' - Entries: 40')

	,'Entries:','- Entries:'),'- -','-')
	,'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' ')
	,'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' '),'  ',' ')

SELECT @Year=year
FROM sJRTCA.TrialList
WHERE TrialListID=@TrialListID

SELECT 
	@text=SUBSTRING([text],CHARINDEX(char(10),[text],CHARINDEX('trouble with the new site so we can make the necessary fixes.',[text],1)+1),CHARINDEX('FLAT RACES',[text],1)),
	@text1=SUBSTRING([text],CHARINDEX('FLAT RACES',[text],1),CHARINDEX('Useful Links',[text],1)-CHARINDEX('FLAT RACES',[text],1))
FROM #tmpBulkResults
where @year>=2012

SELECT 
	@text=SUBSTRING([text],1,CHARINDEX('FLAT RACES',[text],1)),
	@text1=SUBSTRING([text],CHARINDEX('FLAT RACES',[text],1),LEN([text]))
FROM #tmpBulkResults
where @year<=2011

select @text,@text1

CREATE TABLE #tmpResults
	(Results NVARCHAR(MAX))

DECLARE @Delimiter VARCHAR(1000)= CHAR(13) + CHAR(10)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialResults (TrialListID,Results)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),''),'VETERANS, RACING †CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE'),'†','')))
FROM res
OPTION (MAXRECURSION 0)

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@text1, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@text1, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@text1, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialResults (TrialListID,Results)
SELECT @TrialListID, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),'† ',' '),char(10),''),char(12),''),char(13),''),'VETERANS, RACING †CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE')))
FROM res
where LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),'† ',' '),char(10),''),char(12),''),char(13),''))) NOT like '*%' 
	AND LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),'† ',' '),char(10),''),char(12),''),char(13),'')))<>''
OPTION (MAXRECURSION 0)

SELECT * FROM sJRTCA.TrialResults WHERE TrialListID=@TrialListID
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseRawTrialList]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseRawTrialList] (@Year INT,@TrialList NVARCHAR(MAX)) AS

IF object_id('tempdb..#tmpResults') IS NOT NULL
	DROP TABLE #tmpResults

CREATE TABLE #tmpResults
	(Results NVARCHAR(MAX))

DECLARE @Delimiter VARCHAR(1000)= CHAR(13) + CHAR(10)

SELECT @TrialList = @TrialList + CHAR(13) + CHAR(10) + ' end of text'

; WITH numbers AS (
	SELECT ROW_NUMBER() OVER (ORDER BY o.object_id, o2.object_id) AS Number
	FROM sys.objects o
	CROSS JOIN sys.objects o2
), c AS (
	SELECT Number AS CHARBegin, ROW_NUMBER() OVER (ORDER BY number) AS RN
	FROM numbers
	WHERE SUBSTRING(@TrialList, Number, LEN(@Delimiter)) = @Delimiter
), res AS (
	SELECT CHARBegin, CAST(LEFT(@TrialList, charbegin) AS NVARCHAR(MAX)) AS Res, RN
	FROM c
	WHERE rn = 1
	UNION ALL
	SELECT c.CHARBegin, CAST(SUBSTRING(@TrialList, res.CHARBegin, c.CHARBegin - res.CHARBegin) AS NVARCHAR(MAX)), c.RN
	FROM	c
	JOIN res ON c.RN = res.RN + 1
) 
INSERT sJRTCA.TrialList (Year,Trial)
SELECT @Year, LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(res,'  ',' '),char(10),''),char(12),''),char(13),'')))
FROM res
OPTION (MAXRECURSION 0)

SELECT * FROM sJRTCA.TrialList WHERE Year=@Year
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseTrialResults]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseTrialResults] (@TrialListID INT) AS

DECLARE @ResultID INT
DECLARE @Count INT
DECLARE @InnerResultID INT
DECLARE @InnerCount INT
DECLARE @Result VARCHAR(2000)
DECLARE @NextResult VARCHAR(2000)
DECLARE @Division VARCHAR(255)
DECLARE @Championship VARCHAR(255)
DECLARE @Class VARCHAR(255)
DECLARE @OriginalChamp VARCHAR(255)
DECLARE @EntryCount VARCHAR(100)
DECLARE @Place VARCHAR(255)
DECLARE @Dog VARCHAR(255)
DECLARE @Owner VARCHAR(255)
DECLARE @Chairperson VARCHAR(255)
DECLARE @LocationCity VARCHAR(255)
DECLARE @LocationState VARCHAR(255)
DECLARE @ConfJudge VARCHAR(255)
DECLARE @GTGJudge VARCHAR(255)

DECLARE @DivisionID INT
DECLARE @ClassID INT
DECLARE @TrialClassID INT
DECLARE @OwnerID INT
DECLARE @DogID INT

SELECT @ResultID=MIN(TrialResultsID)
FROM sJRTCA.TrialResults
WHERE TrialListID=@TrialListID AND (Results LIKE 'chairman%' or Results LIKE 'chairperson%' or Results LIKE 'admin%strator%' or Results LIKE 'chaired%' or Results LIKE 'judges%')
SELECT @Count=MAX(TrialResultsID)
FROM sJRTCA.TrialResults
WHERE TrialListID=@TrialListID

SELECT @Chairperson=ltrim(rtrim(replace(replace(replace(replace(replace(replace(replace(replace(ltrim(rtrim(tr.Results)),'chairpersons',''),'chairperson',''),'chaired by',''),'chairman',''),'Chairpersed by',''),'Chairped by',''),'† ',''),':','')))
FROM sJRTCA.TrialList tl
LEFT JOIN t.sJRTCA.trialresults tr ON tr.TrialListID=tl.TrialListID
WHERE (tr.Results is null or tr.Results like 'chair%') AND tl.TrialListID=@TrialListID

select 
@LocationCity=ltrim(rtrim(replace(substring(r.Results,1,charindex(',',r.Results)),',',''))),
@LocationState=ltrim(rtrim(substring(r.Results,charindex(',',r.Results)+1,case when r.Results like '%, ' + s.statedescription + '%' then len(s.statedescription) when r.Results like '%, ' + s.stateabbrev + '%' then len(s.stateabbrev) else 1 end+1)))
from sJRTCA.trialresults r
join sJRTCA.triallist tl ON r.TrialListID=tl.TrialListID
join sJRTCA.states s ON 1=1
where r.Results not like '%entries%' 
and r.Results not like '%agility%' 
and r.Results not like '%chair%' 
and r.Results not like '%administrator%' 
and r.Results not like '%judges%' 
and r.Results not like '%owned by%'
and r.Results not like '%1st%'
and r.Results not like '%2nd%'
and r.Results not like '%3rd%'
and r.Results not like '%4th%'
and r.Results not like '%5th%'
and r.Results not like '%6th%'
and r.Results not like '%champion:%'
and r.Results not like '%best:%'
and r.Results not like '%reserve:%'
and (r.Results like '%, ' + s.stateabbrev + '%' or r.Results like '%, ' + s.statedescription + '%')
and tl.TrialListID=@TrialListID

select 
	@ConfJudge=case
		when charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1))>charindex(' ',tr.Results,1) then
			ltrim(rtrim(substring(tr.Results,charindex(' ',tr.Results,1),charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1))-charindex(' ',tr.Results,1))))
		else null end
from t.sJRTCA.triallist tl left join t.sJRTCA.trialresults tr ON tr.TrialListID=tl.TrialListID
where
tr.Results like '%judges:%'
and case
		when charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1))>charindex(' ',tr.Results,1) then
			ltrim(rtrim(substring(tr.Results,charindex(' ',tr.Results,1),charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1))-charindex(' ',tr.Results,1))))
		else null end not like '%judges%'
and tl.TrialListID=@TrialListID

select 
	@GTGJudge=case
		when charindex(', Go-To-Ground',tr.Results,charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)))>charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)) then
			ltrim(rtrim(replace(replace(substring(tr.Results,charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)),charindex(', Go-To-Ground',tr.Results,charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)))-charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1))),', conformation;',''),', conformation,','')))
		else null end
from t.sJRTCA.triallist tl left join t.sJRTCA.trialresults tr ON tr.TrialListID=tl.TrialListID
where
	case
		when charindex(', Go-To-Ground',tr.Results,charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)))>charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)) then
			ltrim(rtrim(replace(replace(substring(tr.Results,charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)),charindex(', Go-To-Ground',tr.Results,charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1)))-charindex(', Conformation',tr.Results,charindex(' ',tr.Results,1))),', conformation;',''),', conformation,','')))
		else null end is not null and
tr.Results like '%judges:%'
and tr.Results like '%go%ground%'
and tl.TrialListID=@TrialListID

UPDATE sJRTCA.TrialList
SET Chairperson=@Chairperson,LocationCity=@LocationCity,LocationState=@LocationState
WHERE TrialListID=@TrialListID

UPDATE sJRTCA.TrialList
SET LocationState=s.StateAbbrev
FROM sJRTCA.TrialList tl
JOIN sJRTCA.States s ON tl.LocationState=s.StateDescription
WHERE tl.TrialListID=@TrialListID

If @ConfJudge IS NOT NULL
	INSERT sJRTCA.TrialList_Judges (TrialListID,DivisionID,JudgeName)
	SELECT @TrialListID,(SELECT DivisionID FROM sJRTCA.Division WHERE DivisionName='CONFORMATION'),@ConfJudge

IF @GTGJudge IS NOT NULL
	INSERT sJRTCA.TrialList_Judges (TrialListID,DivisionID,JudgeName)
	SELECT @TrialListID,(SELECT DivisionID FROM sJRTCA.Division WHERE DivisionName='GO-TO-GROUND'),@GTGJudge

insert sJRTCA.triallist_judges (TrialListID,divisionid,judgename)
select distinct tl.TrialListID,c.divisionid,tj.judgename
from sJRTCA.triallist tl
join sJRTCA.TrialPlacements tp ON tl.TrialListID=tp.TrialListID
join sJRTCA.triallist_judges tj ON tl.TrialListID=tj.TrialListID
join sJRTCA.TrialClass tc ON tp.TrialClassID=tc.TrialClassID
join sJRTCA.Class c ON tc.ClassID=c.ClassID
join sJRTCA.division d ON c.divisionid=d.divisionid
where tl.TrialListID=@TrialListID AND d.divisionname='super earth' and tl.TrialListID not in (select TrialListID from sJRTCA.triallist_judges WHERE divisionid=1249)
and tj.divisionid=1231

PRINT 'TrialListID: ' + CAST(@TrialListID AS VARCHAR(10))

WHILE @ResultID<=@Count
BEGIN
	SELECT @Result=LTRIM(RTRIM(Results))
	FROM sJRTCA.TrialResults
	WHERE TrialResultsID=@ResultID

	PRINT 'Line: ' + @Result + '; Count: ' + CAST(@ResultID AS VARCHAR(100))

	IF RTRIM(LTRIM(@Result)) in 
		('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
		'BALL RETRIEVAL',
		'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
		'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
		'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
		'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
		'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
		'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
		'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
		'GAMES CLASSES',
		'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
		'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
		'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
		'JUMPERS DIVISION',
		'NON-SANCTIONED DIVISION',
		'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
		'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
		'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
		'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
		'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
		'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
		'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
		'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
		'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
		'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
		'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
		OR @Result IN
			('ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING† CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE','6-9mo. PUPPY, RACING CHAMPION & RESERVE','9-12mo. PUPPY, RACING CHAMPION & RESERVE','NON-JRT, UNDER RACING CHAMPION & RESERVE','NON-JRT, OVER RACING CHAMPION & RESERVE',
			'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE','HIGH JUMP HIGH SCORE & RESERVE','BALL TOSS CHAMPION & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE','HIGH JUMP 10 up to 12Ωî Champion & Reserve','HIGH JUMP Over 12Ω up to 15î Champion & Reserve','OBEDIENCE HIGH SCORE & RESERVE','RALLY-O HIGH SCORE & RESERVE','AGILITY CHAMPION & RESERVE','AGILITY CHAMPIONSHIP',
			'SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE')
	BEGIN
		PRINT 'Outer champ/division check: ' + @Result

		IF RTRIM(LTRIM(@Result)) IN ('ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING †CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING †CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING† CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE','6-9mo. PUPPY, RACING CHAMPION & RESERVE','9-12mo. PUPPY, RACING CHAMPION & RESERVE','NON-JRT, UNDER RACING CHAMPION & RESERVE','NON-JRT, OVER RACING CHAMPION & RESERVE',
					'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE','HIGH JUMP HIGH SCORE & RESERVE','BALL TOSS CHAMPION & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE','HIGH JUMP 10 up to 12Ωî Champion & Reserve','HIGH JUMP Over 12Ω up to 15î Champion & Reserve','OBEDIENCE HIGH SCORE & RESERVE','RALLY-O HIGH SCORE & RESERVE','AGILITY CHAMPION & RESERVE','AGILITY CHAMPIONSHIP',
					'SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE')
		BEGIN
			SELECT @Championship=@Result
			SELECT @Class=NULL
			SELECT @EntryCount=NULL
		END
		ELSE
		BEGIN
			SELECT @Division=@Result
			SELECT @Championship=NULL

			SELECT @Division = CASE
				WHEN @Division IN ('AGILILITY','AGILITY DIVISION','AGILITY DIVISON','AGILITY') THEN 'AGILITY DIVISION'
				WHEN @Division IN ('BALL RETRIEVAL') THEN 'BALL RETRIEVAL'
				WHEN @Division IN ('BALL TOSS') THEN 'BALL TOSS'
				WHEN @Division IN ('BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION') THEN 'BARN HUNT'
				WHEN @Division IN ('BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)') THEN 'BRUSH HUNT'
				WHEN @Division IN ('BRUSH HUNT: SATURDAY') THEN 'BRUSH HUNT: SATURDAY'
				WHEN @Division IN ('BRUSH HUNT: SUNDAY') THEN 'BRUSH HUNT: SUNDAY'
				WHEN @Division IN ('CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††') THEN 'CONFORMATION'
				WHEN @Division IN ('DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION') THEN 'DOGGIE FUN ZONE (Non-sanctioned)'
				WHEN @Division IN ('LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)') THEN 'LURE COURSING'
				WHEN @Division IN ('FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS') THEN 'FLAT RACES'
				WHEN @Division IN ('GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG') THEN 'GO-TO-GROUND'
				WHEN @Division IN ('HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE') THEN 'HIGH JUMP'
				WHEN @Division IN ('HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races','STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES') THEN 'STEEPLECHASE RACES'
				WHEN @Division IN ('JUMPERS DIVISION') THEN 'JUMPERS DIVISION'
				WHEN @Division IN ('OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE') THEN 'OBEDIENCE DIVISION'
				WHEN @Division IN ('RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE') THEN 'RALLY OBEDIENCE DIVISION'
				WHEN @Division IN ('SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION') THEN 'SUPER EARTH'
				WHEN @Division IN ('THUNDER TUNNEL','THUNDER TUNNEL DIVISION') THEN 'THUNDER TUNNEL'
				WHEN @Division IN ('TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION') THEN 'TRAILING & LOCATING'
				WHEN @Division IN ('TOP DOG') THEN 'TOP DOG'
				WHEN @Division IN ('TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)') THEN 'TOP GUN'
				WHEN @Division IN ('YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT','YOUTH') THEN 'YOUTH DIVISION'
				ELSE 'UNKNOWN DIVISION!' END
		END

		----display division information
		PRINT 'Division: ' + @Division
		PRINT CASE WHEN ISNULL(@Championship,'')<>'' THEN 'Champ: ' + @Championship ELSE '' END
		SELECT @InnerResultID=@ResultID+1,@InnerCount=@Count

		WHILE @InnerResultID<=@InnerCount
		BEGIN
			IF ISNULL(@NextResult,'')<>''
			BEGIN
				SELECT @InnerResultID-=1
				SELECT @Result=@NextResult
				SELECT @NextResult=NULL
			END
			ELSE
			BEGIN
				SELECT @Result=NULL
				SELECT @NextResult=NULL

				SELECT @Result=REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(Results)),'|',''),'|',''),' ',' '),' :  ',': '),'†',' '),'††††††',' '),'†††††††',' '),'†††††† ',' '),'† ',' ')
				FROM sJRTCA.TrialResults
				WHERE TrialResultsID=@InnerResultID
			END

			IF ISNULL(@Result,'')<>'' AND @Result NOT in 
				('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
				'BALL RETRIEVAL',
				'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
				'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
				'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
				'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
				'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
				'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
				'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
				'GAMES CLASSES',
				'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
				'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
				'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
				'JUMPERS DIVISION',
				'NON-SANCTIONED DIVISION',
				'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
				'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
				'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING †CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING †CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING† CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE',
				'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
				'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
				'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
				'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION','SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE',
				'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
				'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
				'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
				'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				IF @Result LIKE 'Entries%'
				BEGIN
					SELECT @EntryCount=NULL

					IF @Result LIKE 'Entries: %'
						SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries: ',@Result,1)+LEN('Entries: ')+1,LEN(@Result))
					ELSE IF @Result LIKE 'Entries:%'
						SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries:',@Result,1)+LEN('Entries:')+1,LEN(@Result))
					ELSE IF @Result LIKE 'Entries : %'
						SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries : ',@Result,1)+LEN('Entries : '),LEN(@Result))
					ELSE IF @Result LIKE 'Entries :%'
						SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries :',@Result,1)+LEN('Entries :')+1,LEN(@Result))
					ELSE IF @Result LIKE 'Entries :%'
						SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries :',@Result,1)+LEN('Entries :')+1,LEN(@Result))
					ELSE IF @Result LIKE 'Entries %'
						SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries ',@Result,1)+LEN('Entries ')+1,LEN(@Result))
					ELSE IF @Result LIKE 'Entries%'
						SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries',@Result,1)+LEN('Entries')+1,LEN(@Result))

					IF @EntryCount LIKE '% %'
					BEGIN
						SELECT @NextResult = SUBSTRING(@EntryCount,CHARINDEX(' ',@EntryCount)-1,LEN(@EntryCount))
						SELECT @EntryCount = SUBSTRING(@EntryCount,1,CHARINDEX(' ',@EntryCount)-1)
					END
				END
				ELSE IF @Result NOT LIKE '1st%' AND @Result NOT LIKE '2nd%' AND @Result NOT LIKE '3rd%' AND @Result NOT LIKE '4th%' AND @Result NOT LIKE '5th%' AND @Result NOT LIKE '6th%' AND @Result NOT LIKE '%Best:%' AND @Result NOT LIKE '%High Score:%' AND @Result NOT LIKE '%Champ:%' AND @Result NOT LIKE '%Champion:%' AND @Result NOT LIKE '%Reserve:%'
				BEGIN
					IF @Result LIKE '%Entries%'
					BEGIN
						SELECT @EntryCount=NULL
						SELECT @Championship=NULL
						SELECT @OriginalChamp=NULL

						SELECT @Class=CASE 
							WHEN RTRIM(SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-1)) LIKE '%-' THEN SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-4)
							WHEN RTRIM(SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-1)) LIKE '%ñ' THEN SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-4)
--							WHEN RTRIM(SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-2)) LIKE '%ùñ' THEN SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-5)
							ELSE RTRIM(SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-1)) END

						SELECT @Class=replace(@Class,'121/2','12Ω')
						where @Class like '%121/2%'

						SELECT @Class=replace(@Class,'12 1/2','12Ω')
						where @Class like '%12 1/2%'

						SELECT @Class=replace(@Class,'12112','12Ω')
						where @Class like '%12112%'

						SELECT @Class=replace(@Class,'12 112','12Ω')
						where @Class like '%12 112%'

						SELECT @Class=replace(@Class,'121h','12Ω')
						where @Class like '%121h%'

						SELECT @Class=replace(@Class,'12''h','12Ω')
						where @Class like '%12''h%'

						SELECT @Class=replace(@Class,'12h''','12Ω')
						where @Class like '%12h''%'

						SELECT @Class=replace(@Class,'12W''','12Ω')
						where @Class like '%12W''%'

						SELECT @Class=replace(@Class,'121/z','12Ω')
						where @Class like '%121/z%'

						SELECT @Class=replace(@Class,'12.5','12Ω')
						where @Class like '%12.5%'

						SELECT @Class=replace(@Class,'12¬Ω','12Ω')
						where @Class like '%12¬Ω%'

						SELECT @Class=replace(@Class,'olde, r','older, ')
						where @Class like '%olde, r%'

						SELECT @Class=replace(@Class,'‚Ä','')
						where @Class like '%‚Ä%'

						SELECT @Class=replace(@Class,' ì','')
						where @Class like '% ì'

						SELECT @Class=replace(@Class,'15≥','15"')
						where @Class like '%15≥%'

						IF @Result LIKE '%Entries: %'
							SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries: ',@Result,LEN('Entries: ')) + LEN('Entries: ')+1,LEN(@Result)-LEN('Entries: '))
						ELSE IF @Result LIKE '%Entries:%'
							SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries:',@Result,LEN('Entries:')) + LEN('Entries:'),LEN(@Result)-LEN('Entries:'))
						ELSE IF @Result LIKE '%Entries : %'
							SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries : ',@Result,LEN('Entries : ')) + LEN('Entries : '),LEN(@Result)-LEN('Entries : '))
						ELSE IF @Result LIKE '%Entries :%'
							SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries :',@Result,LEN('Entries :')) + LEN('Entries :')+1,LEN(@Result)-LEN('Entries :'))
						ELSE IF @Result LIKE '%Entries :%'
							SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries :',@Result,LEN('Entries :')) + LEN('Entries :'),LEN(@Result)-LEN('Entries :'))
						ELSE IF @Result LIKE '%Entries %'
							SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries ',@Result,LEN('Entries ')) + LEN('Entries ')+1,LEN(@Result)-LEN('Entries '))
						ELSE IF @Result LIKE '%Entries%'
							SELECT @EntryCount=SUBSTRING(@Result,CHARINDEX('Entries',@Result,LEN('Entries')) + LEN('Entries'),LEN(@Result)-LEN('Entries'))

						IF @EntryCount LIKE '% %'
						BEGIN
							SELECT @NextResult = SUBSTRING(@EntryCount,CHARINDEX(' ',@EntryCount)-1,LEN(@EntryCount))
							SELECT @EntryCount = SUBSTRING(@EntryCount,1,CHARINDEX(' ',@EntryCount)-1)
						END
					END
					ELSE
					BEGIN
						SELECT @EntryCount=NULL
						SELECT @Championship=NULL
						SELECT @OriginalChamp=NULL

--						SELECT @Class=@Result
						SELECT @Class=CASE
							WHEN RTRIM(@Result) LIKE '%-' THEN SUBSTRING(@Result,1,LEN(@Result)-2)
--							WHEN RTRIM(@Result) LIKE '%ùñ' THEN SUBSTRING(@Result,1,LEN(@Result)-3)
							ELSE RTRIM(@Result) END
					END
				END
				ELSE IF @Result LIKE '1st%' OR @Result LIKE '2nd%' OR @Result LIKE '3rd%' OR @Result LIKE '4th%' OR @Result LIKE '5th%' OR @Result LIKE '6th%' OR @Result LIKE '%Best:%' OR @Result LIKE '%High Score:%' OR @Result LIKE '%Champ:%' OR @Result LIKE '%Champion:%' OR @Result LIKE '%Reserve:%'
				BEGIN
					IF ISNULL(@Championship,'')<>''
					BEGIN
						SELECT @OriginalChamp=@Championship
						SELECT @Class=RTRIM(SUBSTRING(@Result,1,CASE
							WHEN @Result LIKE '%Champ%' THEN CHARINDEX('Champ',@Result,1)-1
							WHEN @Result LIKE '%Reserve%' THEN CHARINDEX('Reserve',@Result,1)-1
							ELSE LEN(@Result) END)) + ' ' + @Championship
						SELECT @Championship=NULL

						SELECT @Place=SUBSTRING(@Result,CASE
							WHEN @Result LIKE '%Champ%' THEN CHARINDEX('Champ',@Result,1)
							WHEN @Result LIKE '%Reserve%' THEN CHARINDEX('Reserve',@Result,1)
							ELSE LEN(@Result) END,LEN(@Result)-CASE
								WHEN @Result LIKE '%Champ%' THEN CHARINDEX('Champ',@Result,1)
								WHEN @Result LIKE '%Reserve%' THEN CHARINDEX('Reserve',@Result,1)
								ELSE LEN(@Result) END+1)

						SELECT @Dog=REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Place,CHARINDEX(':',@Place,1)+1,LEN(@Place)))),'†† ',''),'† ','')
						SELECT @Owner=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,CHARINDEX('owned by ',@Dog,1)+LEN('owned by '),LEN(@Dog)))),'†† ',''),'† ','')
							ELSE '' END
						SELECT @Dog=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,1,CHARINDEX('owned by',@Dog,1)-1))),'†† ',''),'† ','')
							ELSE @Dog END
						SELECT @Dog=CASE WHEN @Dog LIKE '%,' THEN SUBSTRING(@Dog,1,LEN(@Dog)-1) ELSE @Dog END
						SELECT @Place=RTRIM(SUBSTRING(@Place,1,CHARINDEX(':',@Place,1)-1))
					END
					ELSE
					BEGIN
						SELECT @Place=@Result
						SELECT @Dog=REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Place,CHARINDEX(':',@Place,1)+1,LEN(@Place)))),'†† ',''),'† ','')
						SELECT @Owner=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,CHARINDEX('owned by ',@Dog,1)+LEN('owned by '),LEN(@Dog)))),'†† ',''),'† ','')
							ELSE '' END
						SELECT @Dog=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,1,CHARINDEX('owned by',@Dog,1)-1))),'†† ',''),'† ','')
							ELSE @Dog END
						SELECT @Dog=CASE WHEN @Dog LIKE '%,' THEN SUBSTRING(@Dog,1,LEN(@Dog)-1) ELSE @Dog END
						SELECT @Place=RTRIM(SUBSTRING(@Place,1,CHARINDEX(':',@Place,1)-1))
					END

					SELECT @Class=replace(@Class,'121/2','12Ω')
					where @Class like '%121/2%'

					SELECT @Class=replace(@Class,'12 1/2','12Ω')
					where @Class like '%12 1/2%'

					SELECT @Class=replace(@Class,'12112','12Ω')
					where @Class like '%12112%'

					SELECT @Class=replace(@Class,'12 112','12Ω')
					where @Class like '%12 112%'

					SELECT @Class=replace(@Class,'121h','12Ω')
					where @Class like '%121h%'

					SELECT @Class=replace(@Class,'12''h','12Ω')
					where @Class like '%12''h%'

					SELECT @Class=replace(@Class,'12h''','12Ω')
					where @Class like '%12h''%'

					SELECT @Class=replace(@Class,'12W''','12Ω')
					where @Class like '%12W''%'

					SELECT @Class=replace(@Class,'121/z','12Ω')
					where @Class like '%121/z%'

					SELECT @Class=replace(@Class,'12.5','12Ω')
					where @Class like '%12.5%'

					SELECT @Class=replace(@Class,'12¬Ω','12Ω')
					where @Class like '%12¬Ω%'

					SELECT @Class=replace(@Class,'olde, r','older, ')
					where @Class like '%olde, r%'

					SELECT @Class=replace(@Class,'‚Ä','')
					where @Class like '%‚Ä%'

					SELECT @Class=replace(@Class,' ì','')
					where @Class like '% ì'

					SELECT @Class=replace(@Class,'15≥','15"')
					where @Class like '%15≥%'

					-- display all individual results
					PRINT @InnerResultID
					PRINT 'Division: ' + @Division
					--PRINT CASE WHEN ISNULL(@Championship,'')<>'' THEN 'Champ: ' + ISNULL(@Championship,'') ELSE '' END
					PRINT 'Class: ' + ISNULL(@Class,'')
					PRINT CASE WHEN ISNULL(@EntryCount,'')<>'' THEN 'Entry Count: ' + LTRIM(RTRIM(@EntryCount)) ELSE '' END
					PRINT 'Place: ' + @Place
					PRINT 'Dog: ' + @Dog
					PRINT 'Owner: ' + ISNULL(@Owner,'')
					PRINT ''

					IF NOT EXISTS (SELECT DivisionID FROM sJRTCA.Division WHERE DivisionName=LTRIM(RTRIM(@Division)))
						INSERT sJRTCA.Division (DivisionName)
						SELECT LTRIM(RTRIM(@Division))

					SELECT @DivisionID=DivisionID FROM sJRTCA.Division WHERE DivisionName=LTRIM(RTRIM(@Division))

					IF NOT EXISTS (SELECT ClassID FROM sJRTCA.Class WHERE DivisionID=@DivisionID AND ClassName=LTRIM(RTRIM(@Class)))
						INSERT sJRTCA.Class (DivisionID,ClassName)
						SELECT @DivisionID,LTRIM(RTRIM(@Class))

					SELECT @ClassID=ClassID FROM sJRTCA.Class WHERE DivisionID=@DivisionID AND ClassName=LTRIM(RTRIM(@Class))

					IF NOT EXISTS (SELECT TrialClassID FROM sJRTCA.TrialClass WHERE ClassID=@ClassID AND TrialListID=@TrialListID)
						INSERT sJRTCA.TrialClass (ClassID,TrialListID,EntryCount)
						SELECT @ClassID,@TrialListID,CASE WHEN ISNULL(@EntryCount,'')='' THEN 0 ELSE CAST(LTRIM(RTRIM(@EntryCount)) AS INT) END

					SELECT @TrialClassID=TrialClassID FROM sJRTCA.TrialClass WHERE ClassID=@ClassID AND TrialListID=@TrialListID

					IF NOT EXISTS (SELECT OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner)))
						INSERT sAll.Owner (OwnerName)
						SELECT LTRIM(RTRIM(@Owner))

					SELECT @OwnerID=OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner))

					IF NOT EXISTS (SELECT DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog)))
						INSERT sAll.Dog (OwnerID,DogName)
						SELECT @OwnerID, LTRIM(RTRIM(@Dog))

					SELECT @DogID=DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog))

					IF NOT EXISTS (SELECT TrialPlacementsID FROM sJRTCA.TrialPlacements WHERE TrialListID=@TrialListID AND TrialClassID=@TrialClassID AND DogID=@DogID)
						INSERT sJRTCA.TrialPlacements (TrialListID,TrialClassID,DogID,Result)
						SELECT @TrialListID,@TrialClassID,@DogID,@Place

					SELECT @Championship=@OriginalChamp
				END

				SELECT @InnerResultID+=1
			END
			ELSE IF ISNULL(@Result,'')<>'' AND RTRIM(LTRIM(@Result)) IN 
					('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
					'BALL RETRIEVAL',
					'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
					'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
					'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
					'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
					'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
					'LURE COURSING','FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
					'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
					'GAMES CLASSES',
					'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
					'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
					'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
					'JUMPERS DIVISION',
					'NON-SANCTIONED DIVISION',
					'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
					'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
					'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE',
					'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
					'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
					'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
					'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION','SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE',
					'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
					'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
					'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
					'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				--SELECT @InnerResultID=@InnerCount+1
				SELECT @InnerCount=@InnerResultID-2
				SELECT @InnerResultID-=1
			END
			ELSE IF ISNULL(@Result,'')=''
				SELECT @InnerResultID+=1

			--SELECT @InnerResultID+=1
		END
	END

	--print 'InnerResultID: ' + CAST(@innerresultid AS VARCHAR(10))
	--print 'ResultID: ' + CAST(@resultid AS VARCHAR(10))
	--print 'InnerCount: ' + CAST(@innercount AS VARCHAR(10))
	--print 'Count: ' + CAST(@count AS VARCHAR(10))
	--print 'Result: ' + @result
	IF ISNULL(@InnerResultID,0)<>0-->@ResultID
		SELECT @ResultID=@InnerResultID

	SELECT @ResultID+=1
END

update sJRTCA.Class
set ClassName=replace(ClassName,'121/2','12Ω')
where ClassName like '%121/2%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12 1/2','12Ω')
where ClassName like '%12 1/2%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12112','12Ω')
where ClassName like '%12112%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12 112','12Ω')
where ClassName like '%12 112%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'121h','12Ω')
where ClassName like '%121h%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12''h','12Ω')
where ClassName like '%12''h%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12h''','12Ω')
where ClassName like '%12h''%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12W''','12Ω')
where ClassName like '%12W''%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'121/z','12Ω')
where ClassName like '%121/z%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12.5','12Ω')
where ClassName like '%12.5%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'12¬Ω','12Ω')
where ClassName like '%12¬Ω%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'olde, r','older, ')
where ClassName like '%olde, r%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'‚Ä','')
where ClassName like '%‚Ä%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,' ì','')
where ClassName like '% ì' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.Class
set ClassName=replace(ClassName,'15≥','15"')
where ClassName like '%15≥%' and ClassID in (select ClassID from sJRTCA.TrialClass WHERE TrialListID=@TrialListID)

update sJRTCA.TrialPlacements
set result='Champion'
from sJRTCA.TrialPlacements tp
join sJRTCA.TrialClass tc ON tp.TrialClassID=tc.TrialClassID
join sJRTCA.Class c ON tc.ClassID=c.ClassID
where c.ClassName like '%best%open%terrier%' and tp.Result='best' and tp.TrialListID=@TrialListID

update sJRTCA.TrialPlacements
set result='Champion'
from sJRTCA.TrialPlacements tp
join sJRTCA.TrialClass tc ON tp.TrialClassID=tc.TrialClassID
join sJRTCA.Class c ON tc.ClassID=c.ClassID
where c.ClassName like '%puppy%conformation%champion%' and tp.Result='best' and tp.TrialListID=@TrialListID

update sJRTCA.TrialPlacements
set result='Champion'
from sJRTCA.TrialPlacements tp
join sJRTCA.TrialClass tc ON tp.TrialClassID=tc.TrialClassID
join sJRTCA.Class c ON tc.ClassID=c.ClassID
where c.ClassName like '%working%terrier%champion%' and tp.Result='best' and tp.TrialListID=@TrialListID

update sJRTCA.trialplacements
set result=CASE WHEN tp.Result='1st' THEN 'Champion' WHEN tp.Result='2nd' THEN 'Reserve' ELSE NULL END
from sJRTCA.Class c
join sJRTCA.Division d on c.DivisionID=d.DivisionID
join sJRTCA.TrialClass tc on c.ClassID=tc.ClassID
join sJRTCA.TrialPlacements tp on tc.TrialClassID=tp.TrialClassID
join sJRTCA.TrialList tl on tp.TrialListID=tl.TrialListID
where tp.Result in ('1st','2nd') and (c.classname like '%championship%' or c.classname like '%certificate%') and d.divisionname='go-to-ground' and tl.TrialListID=@TrialListID and tl.[Year]>1998

update sJRTCA.trialplacements
set result=CASE WHEN tp.result='1st' THEN 'Best' WHEN tp.result='2nd' THEN 'Reserve' ELSE NULL END
from sJRTCA.class c
join sJRTCA.division d on c.divisionid=d.divisionid
join sJRTCA.trialclass tc on c.classid=tc.classid
join sJRTCA.trialplacements tp on tc.trialclassid=tp.trialclassid
join sJRTCA.triallist tl on tp.triallistid=tl.triallistid
where tp.result in ('1st','2nd') and (c.classname like 'best%') and d.divisionname='conformation'
GO

/****** Object:  StoredProcedure [sJRTCA].[spParseTrialResultsNoEntries]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spParseTrialResultsNoEntries] (@TrialListID INT) AS

DECLARE @ResultID INT
DECLARE @Count INT
DECLARE @InnerResultID INT
DECLARE @InnerCount INT
DECLARE @Result VARCHAR(2000)
DECLARE @NextResult VARCHAR(2000)
DECLARE @Division VARCHAR(255)
DECLARE @Championship VARCHAR(255)
DECLARE @Class VARCHAR(255)
DECLARE @OriginalChamp VARCHAR(255)
DECLARE @EntryCount VARCHAR(100)
DECLARE @Place VARCHAR(255)
DECLARE @Dog VARCHAR(255)
DECLARE @Owner VARCHAR(255)
DECLARE @Chairperson VARCHAR(255)
DECLARE @ConfJudge VARCHAR(255)
DECLARE @GTGJudge VARCHAR(255)

DECLARE @DivisionID INT
DECLARE @ClassID INT
DECLARE @TrialClassID INT
DECLARE @OwnerID INT
DECLARE @DogID INT

SELECT @ResultID=MIN(TrialResultsID)
FROM sJRTCA.TrialResults
WHERE TrialListID=@TrialListID AND (Results LIKE 'chairperson%' or Results LIKE 'admin%strator%' or Results LIKE 'chaired%' or Results LIKE 'judges%')
SELECT @Count=MAX(TrialResultsID)
FROM sJRTCA.TrialResults
WHERE TrialListID=@TrialListID

SELECT @Chairperson=ltrim(rtrim(replace(replace(replace(replace(replace(replace(replace(replace(ltrim(rtrim(tr.results)),'chairpersons',''),'chairperson',''),'chaired by',''),'chairman',''),'Chairpersed by',''),'Chairped by',''),'† ',''),':','')))
FROM sJRTCA.TrialList tl
LEFT JOIN t.sjrtca.trialresults tr on tr.triallistid=tl.triallistid
WHERE (tr.results is null or tr.results like 'chair%') AND tl.triallistid=@TrialListID

select 
	@ConfJudge=case
		when charindex(', Conformation',tr.results,charindex(' ',tr.results,1))>charindex(' ',tr.results,1) then
			ltrim(rtrim(substring(tr.results,charindex(' ',tr.results,1),charindex(', Conformation',tr.results,charindex(' ',tr.results,1))-charindex(' ',tr.results,1))))
		else null end
from t.sjrtca.triallist tl left join t.sjrtca.trialresults tr on tr.triallistid=tl.triallistid
where
tr.results like '%judges:%'
and case
		when charindex(', Conformation',tr.results,charindex(' ',tr.results,1))>charindex(' ',tr.results,1) then
			ltrim(rtrim(substring(tr.results,charindex(' ',tr.results,1),charindex(', Conformation',tr.results,charindex(' ',tr.results,1))-charindex(' ',tr.results,1))))
		else null end not like '%judges%'
and tl.triallistid=@TrialListID

select 
	@GTGJudge=case
		when charindex(', Go-To-Ground',tr.results,charindex(', Conformation',tr.results,charindex(' ',tr.results,1)))>charindex(', Conformation',tr.results,charindex(' ',tr.results,1)) then
			ltrim(rtrim(replace(replace(substring(tr.results,charindex(', Conformation',tr.results,charindex(' ',tr.results,1)),charindex(', Go-To-Ground',tr.results,charindex(', Conformation',tr.results,charindex(' ',tr.results,1)))-charindex(', Conformation',tr.results,charindex(' ',tr.results,1))),', conformation;',''),', conformation,','')))
		else null end
from t.sjrtca.triallist tl left join t.sjrtca.trialresults tr on tr.triallistid=tl.triallistid
where
	case
		when charindex(', Go-To-Ground',tr.results,charindex(', Conformation',tr.results,charindex(' ',tr.results,1)))>charindex(', Conformation',tr.results,charindex(' ',tr.results,1)) then
			ltrim(rtrim(replace(replace(substring(tr.results,charindex(', Conformation',tr.results,charindex(' ',tr.results,1)),charindex(', Go-To-Ground',tr.results,charindex(', Conformation',tr.results,charindex(' ',tr.results,1)))-charindex(', Conformation',tr.results,charindex(' ',tr.results,1))),', conformation;',''),', conformation,','')))
		else null end is not null and
tr.results like '%judges:%'
and tr.results like '%go%ground%'
and tl.triallistid=@TrialListID

UPDATE sJRTCA.TrialList
SET Chairperson=@Chairperson
WHERE TrialListID=@TrialListID

INSERT sJRTCA.TrialList_Judges (TrialListID,DivisionID,JudgeName)
SELECT @TrialListID,(SELECT DivisionID FROM sJRTCA.Division WHERE DivisionName='CONFORMATION'),@ConfJudge

INSERT sJRTCA.TrialList_Judges (TrialListID,DivisionID,JudgeName)
SELECT @TrialListID,(SELECT DivisionID FROM sJRTCA.Division WHERE DivisionName='GO-TO-GROUND'),@GTGJudge

PRINT 'TrialListID: ' + CAST(@TrialListID AS VARCHAR(10))

WHILE @ResultID<=@Count
BEGIN
	SELECT @Result=LTRIM(RTRIM(Results))
	FROM sJRTCA.TrialResults
	WHERE TrialResultsID=@ResultID

	PRINT 'Line: ' + @Result + '; Count: ' + CAST(@ResultID AS VARCHAR(100))

	IF RTRIM(LTRIM(@Result)) in 
		('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
		'BALL RETRIEVAL',
		'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
		'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
		'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
		'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
		'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
		'FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
		'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
		'GAMES CLASSES',
		'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
		'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
		'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
		'JUMPERS DIVISION',
		'NON-SANCTIONED DIVISION',
		'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
		'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
		'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE',
		'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
		'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
		'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
		'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION',
		'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
		'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
		'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
		'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
		OR @Result IN
			('ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING† CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE','6-9mo. PUPPY, RACING CHAMPION & RESERVE','9-12mo. PUPPY, RACING CHAMPION & RESERVE','NON-JRT, UNDER RACING CHAMPION & RESERVE','NON-JRT, OVER RACING CHAMPION & RESERVE',
			'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE','HIGH JUMP HIGH SCORE & RESERVE','BALL TOSS CHAMPION & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE','HIGH JUMP 10 up to 12Ωî Champion & Reserve','HIGH JUMP Over 12Ω up to 15î Champion & Reserve','OBEDIENCE HIGH SCORE & RESERVE','RALLY-O HIGH SCORE & RESERVE','AGILITY CHAMPION & RESERVE','AGILITY CHAMPIONSHIP',
			'SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE')
	BEGIN
		PRINT 'Outer champ/division check: ' + @Result

		IF RTRIM(LTRIM(@Result)) IN ('ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING †CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING †CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING† CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE','NON-JRT, RACING CHAMPION & RESERVE','6-9mo. PUPPY, RACING CHAMPION & RESERVE','9-12mo. PUPPY, RACING CHAMPION & RESERVE','NON-JRT, UNDER RACING CHAMPION & RESERVE','NON-JRT, OVER RACING CHAMPION & RESERVE',
					'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE','HIGH JUMP HIGH SCORE & RESERVE','BALL TOSS CHAMPION & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE','HIGH JUMP 10 up to 12Ωî Champion & Reserve','HIGH JUMP Over 12Ω up to 15î Champion & Reserve','OBEDIENCE HIGH SCORE & RESERVE','RALLY-O HIGH SCORE & RESERVE','AGILITY CHAMPION & RESERVE','AGILITY CHAMPIONSHIP',
					'SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE')
		BEGIN
			SELECT @Championship=@Result
			SELECT @Class=NULL
			SELECT @EntryCount=0
		END
		ELSE
		BEGIN
			SELECT @Division=@Result
			SELECT @Championship=NULL
		END

		----display division information
		PRINT 'Division: ' + @Division
		PRINT CASE WHEN ISNULL(@Championship,'')<>'' THEN 'Champ: ' + @Championship ELSE '' END
		SELECT @InnerResultID=@ResultID+1,@InnerCount=@Count

		WHILE @InnerResultID<=@InnerCount
		BEGIN
			IF ISNULL(@NextResult,'')<>''
			BEGIN
				SELECT @InnerResultID-=1
				SELECT @Result=@NextResult
				SELECT @NextResult=NULL
			END
			ELSE
			BEGIN
				SELECT @Result=NULL
				SELECT @NextResult=NULL

				SELECT @Result=REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(Results)),'|',''),'|',''),' ',' '),' :  ',': '),'†',' '),'††††††',' '),'†††††††',' '),'†††††† ',' '),'† ',' ')
				FROM sJRTCA.TrialResults
				WHERE TrialResultsID=@InnerResultID
			END

			IF ISNULL(@Result,'')<>'' AND @Result NOT in 
				('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
				'BALL RETRIEVAL',
				'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
				'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
				'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
				'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
				'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
				'FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
				'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
				'GAMES CLASSES',
				'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
				'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
				'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
				'JUMPERS DIVISION',
				'NON-SANCTIONED DIVISION',
				'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
				'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
				'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING †CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING †CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING† CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE',
				'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
				'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
				'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
				'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION','SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE',
				'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
				'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
				'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
				'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				IF @Result NOT LIKE '1st%' AND @Result NOT LIKE '2nd%' AND @Result NOT LIKE '3rd%' AND @Result NOT LIKE '4th%' AND @Result NOT LIKE '5th%' AND @Result NOT LIKE '6th%' AND @Result NOT LIKE '%Best:%' AND @Result NOT LIKE '%High Score:%' AND @Result NOT LIKE '%Champ:%' AND @Result NOT LIKE '%Champion:%' AND @Result NOT LIKE '%Reserve:%'
				BEGIN
					SELECT @EntryCount=0
					SELECT @Championship=NULL
					SELECT @OriginalChamp=NULL

--						SELECT @Class=@Result
					SELECT @Class=CASE
						WHEN RTRIM(@Result) LIKE '%-' THEN SUBSTRING(@Result,1,LEN(@Result)-2)
--							WHEN RTRIM(@Result) LIKE '%ùñ' THEN SUBSTRING(@Result,1,LEN(@Result)-3)
						ELSE RTRIM(@Result) END
				END
				ELSE IF @Result LIKE '1st%' OR @Result LIKE '2nd%' OR @Result LIKE '3rd%' OR @Result LIKE '4th%' OR @Result LIKE '5th%' OR @Result LIKE '6th%' OR @Result LIKE '%Best:%' OR @Result LIKE '%High Score:%' OR @Result LIKE '%Champ:%' OR @Result LIKE '%Champion:%' OR @Result LIKE '%Reserve:%'
				BEGIN
					IF ISNULL(@Championship,'')<>''
					BEGIN
						SELECT @OriginalChamp=@Championship
						SELECT @Class=RTRIM(SUBSTRING(@Result,1,CASE
							WHEN @Result LIKE '%Champ%' THEN CHARINDEX('Champ',@Result,1)-1
							WHEN @Result LIKE '%Reserve%' THEN CHARINDEX('Reserve',@Result,1)-1
							ELSE LEN(@Result) END)) + ' ' + @Championship
						SELECT @Championship=NULL

						SELECT @Place=SUBSTRING(@Result,CASE
							WHEN @Result LIKE '%Champ%' THEN CHARINDEX('Champ',@Result,1)
							WHEN @Result LIKE '%Reserve%' THEN CHARINDEX('Reserve',@Result,1)
							ELSE LEN(@Result) END,LEN(@Result)-CASE
								WHEN @Result LIKE '%Champ%' THEN CHARINDEX('Champ',@Result,1)
								WHEN @Result LIKE '%Reserve%' THEN CHARINDEX('Reserve',@Result,1)
								ELSE LEN(@Result) END+1)

						SELECT @Dog=REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Place,CHARINDEX(':',@Place,1)+1,LEN(@Place)))),'†† ',''),'† ','')
						SELECT @Owner=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,CHARINDEX('owned by ',@Dog,1)+LEN('owned by '),LEN(@Dog)))),'†† ',''),'† ','')
							ELSE '' END
						SELECT @Dog=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,1,CHARINDEX('owned by',@Dog,1)-1))),'†† ',''),'† ','')
							ELSE @Dog END
						SELECT @Dog=CASE WHEN @Dog LIKE '%,' THEN SUBSTRING(@Dog,1,LEN(@Dog)-1) ELSE @Dog END
						SELECT @Place=RTRIM(SUBSTRING(@Place,1,CHARINDEX(':',@Place,1)-1))
					END
					ELSE
					BEGIN
						SELECT @Place=@Result
						SELECT @Dog=REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Place,CHARINDEX(':',@Place,1)+1,LEN(@Place)))),'†† ',''),'† ','')
						SELECT @Owner=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,CHARINDEX('owned by ',@Dog,1)+LEN('owned by '),LEN(@Dog)))),'†† ',''),'† ','')
							ELSE '' END
						SELECT @Dog=CASE WHEN @Dog LIKE '%owned by%' THEN
							REPLACE(REPLACE(LTRIM(RTRIM(SUBSTRING(@Dog,1,CHARINDEX('owned by',@Dog,1)-1))),'†† ',''),'† ','')
							ELSE @Dog END
						SELECT @Dog=CASE WHEN @Dog LIKE '%,' THEN SUBSTRING(@Dog,1,LEN(@Dog)-1) ELSE @Dog END
						SELECT @Place=RTRIM(SUBSTRING(@Place,1,CHARINDEX(':',@Place,1)-1))
					END

					-- display all individual results
					PRINT @InnerResultID
					PRINT 'Division: ' + @Division
					--PRINT CASE WHEN ISNULL(@Championship,'')<>'' THEN 'Champ: ' + ISNULL(@Championship,'') ELSE '' END
					PRINT 'Class: ' + ISNULL(@Class,'')
					PRINT CASE WHEN ISNULL(@EntryCount,'')<>'' THEN 'Entry Count: ' + LTRIM(RTRIM(@EntryCount)) ELSE '' END
					PRINT 'Place: ' + @Place
					PRINT 'Dog: ' + @Dog
					PRINT 'Owner: ' + ISNULL(@Owner,'')
					PRINT ''

					IF NOT EXISTS (SELECT DivisionID FROM sJRTCA.Division WHERE DivisionName=LTRIM(RTRIM(@Division)))
						INSERT sJRTCA.Division (DivisionName)
						SELECT LTRIM(RTRIM(@Division))

					SELECT @DivisionID=DivisionID FROM sJRTCA.Division WHERE DivisionName=LTRIM(RTRIM(@Division))

					IF NOT EXISTS (SELECT ClassID FROM sJRTCA.Class WHERE DivisionID=@DivisionID AND ClassName=LTRIM(RTRIM(@Class)))
						INSERT sJRTCA.Class (DivisionID,ClassName)
						SELECT @DivisionID,LTRIM(RTRIM(@Class))

					SELECT @ClassID=ClassID FROM sJRTCA.Class WHERE DivisionID=@DivisionID AND ClassName=LTRIM(RTRIM(@Class))

					IF NOT EXISTS (SELECT TrialClassID FROM sJRTCA.TrialClass WHERE ClassID=@ClassID AND TrialListID=@TrialListID)
						INSERT sJRTCA.TrialClass (ClassID,TrialListID,EntryCount)
						SELECT @ClassID,@TrialListID,CASE WHEN ISNULL(@EntryCount,'')='' THEN 0 ELSE CAST(LTRIM(RTRIM(@EntryCount)) AS INT) END

					SELECT @TrialClassID=TrialClassID FROM sJRTCA.TrialClass WHERE ClassID=@ClassID AND TrialListID=@TrialListID

					IF NOT EXISTS (SELECT OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner)))
						INSERT sAll.Owner (OwnerName)
						SELECT LTRIM(RTRIM(@Owner))

					SELECT @OwnerID=OwnerID FROM sAll.Owner WHERE OwnerName=LTRIM(RTRIM(@Owner))

					IF NOT EXISTS (SELECT DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog)))
						INSERT sAll.Dog (OwnerID,DogName)
						SELECT @OwnerID, LTRIM(RTRIM(@Dog))

					SELECT @DogID=DogID FROM sAll.Dog WHERE OwnerID=@OwnerID AND DogName=LTRIM(RTRIM(@Dog))

					IF NOT EXISTS (SELECT TrialPlacementsID FROM sJRTCA.TrialPlacements WHERE TrialListID=@TrialListID AND TrialClassID=@TrialClassID AND DogID=@DogID)
						INSERT sJRTCA.TrialPlacements (TrialListID,TrialClassID,DogID,Result)
						SELECT @TrialListID,@TrialClassID,@DogID,@Place

					SELECT @Championship=@OriginalChamp
				END

				SELECT @InnerResultID+=1
			END
			ELSE IF ISNULL(@Result,'')<>'' AND RTRIM(LTRIM(@Result)) IN 
					('AGILILITY','AGILITY DIVISION','AGILITY DIVISON',
					'BALL RETRIEVAL',
					'BALL TOSS','BALL TOSS CHAMPION & RESERVE',
					'BARN HUNT','BARN HUNT (Non-Sanctioned)','BARN HUNT DIVISION (Non-Sanctioned)','BARN HUNT DIVISION',
					'BRUSH HUNT','BRUSH HUNT DIVISION','BRUSH HUNT (NON SANCTIONED)','BRUSH HUNT: SATURDAY','BRUSH HUNT: SUNDAY',
					'CONFORMATION','CONFORMATION DIVISION:','CONFORMATION DIVISION','CONFORMATION DIVISON','CONFORMATION DIVISION †††††††††',
					'DOGGIE FUN ZONE (Non-sanctioned)','DOGGIE FUN ZONE','DOGGIE FUN ZONE DIVISION (Non-sanctioned)','DOGGIE FUN ZONE DIVISION',
					'FIELD LURE COURSING','FIELD LURE COURSING (NON-SANCTIONED)',--'Friday Lure Coursing Champion & Reserve','Saturday Lure Coursing Champion & Reserve','Sunday Lure Coursing Champion & Reserve','Lure Coursing Friday Champion & Reserve','Lure Coursing Saturday Champion & Reserve','Lure Coursing Sunday Champion & Reserve',
					'FLAT RACES:','FLAT RACES','FLAT RACING','FLATS RACING','FLATS',
					'GAMES CLASSES',
					'GO-TO GROUND','GO-TO- GROUND','GO-TO-GOUND DIVISION','Go-To-Ground','GO-TO-GROUND DIVISIION','GO-TO-GROUND DIVISION','GO-TO-GROUND DIVISON','GO-TO-TO-GROUND','GTG',
					'HIGH JUMP','HIGH JUMP DIVISION','SUNDAY HIGH JUMP','HIGH JUMP HIGH SCORE & RESERVE',
					'HURDLE','Hurdle Race','HURDLE RACES','HURDLES','Hurdles Races',
					'JUMPERS DIVISION',
					'NON-SANCTIONED DIVISION',
					'OBEDIENCE','OBEDIENCE DIVISION','OBEDIENCE DIVISON','OBEDIENCE HIGH SCORE & RESERVE',
					'RACING','RACING DIVISION','RACING DIVISION','RACING DIVISION FLAT RACES','RACING DIVISON',
					'ADULT RACING CHAMPION & RESERVE','ADULT, RACING CHAMPION & RESERVE','ADULT, under 10 ñ 12 Ωî RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE','PUPPY RACING CHAMPION & RESERVE†','PUPPY RACING CHAMPION & RESERVE, 4 UP TO 6 MONTHS','Puppy Racing Champion Under 12.5"& Reserve','PUPPY, RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION & RESERVE','SENIORS RACING CHAMPION AND RESERVE','SENIORS RACING† CHAMPION & RESERVE','SENIORS, 10 up to 12Ω", RACING CHAMPION & RESERVE','SENIORS, 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, over 12Ω up to 15", RACING CHAMPION & RESERVE','SENIORS, RACING CHAMPION & RESERVE','SENIORS, RACING† CHAMPION & RESERVE','SENIORS, RACING†CHAMPION & RESERVE','VETERANS RACING CHAMPION & RESERVE','Veterans Racing Champion & Reserve','VETERANS, 10 up to 12Ω", RACING CHAMPION & RESERVE','VETERANS, 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, over 12Ω up to 15", RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERANS, RACING†CHAMPION & RESERVE','VETERAN RACING CHAMPION & RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERVE','SENIOR RACING 10-12 Ωî CHAMPION & RESERVE','SENIOR RACING 12 Ω-15î CHAMPION & RESERVE','SENIOR, RACING CHAMPION & RESERVE','SENIORS, RACING  CHAMPION & RESERVE','VETERANS, RACING  CHAMPION & RESERVE','VETERAN, RACING CHAMPION & RESERVE','SENIOR RACING CHAMPION & RESERE','SENIOR VETERAN CHAMPION & RESERVE','PUPPY RACING CHAMPIONSHIP','ADULT RACING CHAMPIONSHIP','VETERAN RACING CHAMPIONSHIP','SENIOR RACING CHAMPIONSHIP','SENIOR RACING CHAMPION AND RESERVE','SENIOR VETERAN RACING CHAMPION & RESERVE','SENIOR VETERANS RACING CHAMPION & RESERVE','NON-JRT RACING CHAMPION & RESERVE',
					'AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE','VETERANS AGILITY HIGH SCORE CHAMPION & RESERVE','VETERAN/SENIOR AGILITY HIGH SCORE CHAMPION & RESERVE',
					'RALLY OBEDIENCE','RALLY OBEDIENCE DIVISION','RALLY-O','RALLY-OBEDIENCE','RALLY-O HIGH SCORE & RESERVE',
					'STEEPLECHASE RACES','STEELPECHASE RACES','STEEPLECHASE','STEEPLECHASE RACE','STEEPLECHASE RACES',
					'SUPER EARTH','SUPER EARTH DIVISION','SUPER EARTH GTG DIVISION','Super Earth Stakes','SUPER GTG','SUPER SENIOR','SUPEREARTH','SUPER EARTH GO-TO-GROUND DIVISION','SUPER EARTH CHAMPION & RESERVE','SUPER EARTH FASTEST TIME CHAMPION & RESERVE',
					'THUNDER TUNNEL','THUNDER TUNNEL DIVISION',--'FRIDAY HIGH SCORE & RESERVE','SATURDAY HIGH SCORE & RESERVE','THUNDER TUNNEL HIGH SCORE & RESERVE',
					'TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION','TRAILING','TRAILING & LOCATING','TRAILING & LOCATING DIVISION','TRAILING & LOCATING DIVISON','TRAILING/LOCATING DIVISION',
					'TOP DOG','TOP GUN','TOP GUN CHALLENGE','TOP DOG (NON-SANCTIONED)',
					'YOUTH DIVISION','YOUTH DIVISON','YOUTH HIGH POINT')
			BEGIN
				--SELECT @InnerResultID=@InnerCount+1
				SELECT @InnerCount=@InnerResultID-2
				SELECT @InnerResultID-=1
			END
			ELSE IF ISNULL(@Result,'')=''
				SELECT @InnerResultID+=1

			--SELECT @InnerResultID+=1
		END
	END

	--print 'InnerResultID: ' + CAST(@innerresultid AS VARCHAR(10))
	--print 'ResultID: ' + CAST(@resultid AS VARCHAR(10))
	--print 'InnerCount: ' + CAST(@innercount AS VARCHAR(10))
	--print 'Count: ' + CAST(@count AS VARCHAR(10))
	--print 'Result: ' + @result
	IF ISNULL(@InnerResultID,0)<>0-->@ResultID
		SELECT @ResultID=@InnerResultID

	SELECT @ResultID+=1
END
GO

/****** Object:  StoredProcedure [sJRTCA].[spReadPath]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spReadPath] (@BasePath VARCHAR(255) = 'C:\Trial Data') AS

IF OBJECT_ID('tempdb..#DirectoryTree') IS NOT NULL
      DROP TABLE #DirectoryTree;

TRUNCATE TABLE sJRTCA.ReadPath

DECLARE
      @Path varchar(1000)
      ,@FullPath varchar(2000)
      ,@Id int;

CREATE TABLE #DirectoryTree (
       id int IDENTITY(1,1)
      ,fullpath varchar(2000)
      ,subdirectory nvarchar(512)
      ,depth int
      ,isfile bit);

--Create a clustered index to keep everything in order.
ALTER TABLE #DirectoryTree
ADD CONSTRAINT PK_DirectoryTree PRIMARY KEY CLUSTERED (id);

--Populate the table using the initial base path.
INSERT #DirectoryTree (subdirectory,depth,isfile)
EXEC master.sys.xp_dirtree @BasePath,1,1;

UPDATE #DirectoryTree SET fullpath = @BasePath;

--Loop through the table as long as there are still folders to process.
WHILE EXISTS (SELECT id FROM #DirectoryTree WHERE isfile = 0)
BEGIN
      --Select the first row that is a folder.
      SELECT TOP (1)
             @Id = id
            ,@FullPath = fullpath
            ,@Path = @BasePath + '\' + subdirectory
      FROM #DirectoryTree WHERE isfile = 0;

      IF @FullPath = @Path
      BEGIN
            --Do this section if the we are still in the same folder.
            INSERT #DirectoryTree (subdirectory,depth,isfile)
            EXEC master.sys.xp_dirtree @Path,1,1;

            UPDATE #DirectoryTree
            SET fullpath = @Path
            WHERE fullpath IS NULL;

            --Delete the processed folder.
            DELETE FROM #DirectoryTree WHERE id = @Id;
      END
      ELSE
      BEGIN
            --Do this section if we need to jump down into another subfolder.
            SET @BasePath = @FullPath;

            --Select the first row that is a folder.
            SELECT TOP (1)
                   @Id = id
                  ,@FullPath = fullpath
                  ,@Path = @BasePath + '\' + subdirectory
            FROM #DirectoryTree WHERE isfile = 0;

            INSERT #DirectoryTree (subdirectory,depth,isfile)
            EXEC master.sys.xp_dirtree @Path,1,1;

            UPDATE #DirectoryTree
            SET fullpath = @Path
            WHERE fullpath IS NULL;

            --Delete the processed folder.
            DELETE FROM #DirectoryTree WHERE id = @Id;
      END
END

--Output the results.
INSERT sJRTCA.ReadPath (Path)
SELECT fullpath + '\' + subdirectory AS 'CompleteFileList'
FROM #DirectoryTree
WHERE subdirectory like '%txt'
ORDER BY fullpath,subdirectory
GO

/****** Object:  StoredProcedure [sJRTCA].[spSireCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



CREATE PROCEDURE [sJRTCA].[spSireCleanup] (@MatchScore FLOAT=.9,@DogName varchar(255)=NULL) AS
	EXEC [sJRTCA].[spFuzzyMatch_Sire] @MatchScore,@DogName

	; WITH MinMatch AS (
		SELECT DISTINCT 
			m.SireID,m.Sire,d.Sire AS DogSire,d.Dam AS DogDam,d1.Sire AS NewDogSire,d1.Dam AS NewDogDam,Min(m.MatchScore) OVER (PARTITION BY m.SireID,m.Sire) AS MatchScore
		FROM [sJRTCA].[Sire_TempMatch] m
		LEFT JOIN sAll.Dog d ON m.Sire=d.DogName
		LEFT JOIN sAll.Dog d1 ON m.DogID=d1.DogID
		where m.SireID<>m.DogID
	)
	SELECT DISTINCT 
		'UPDATE ' + DB_NAME() + '.sAll.Dog SET Sire=''' + REPLACE(t.DogName,'''','''''') + ''',SireID=' + CAST(m.SireID AS VARCHAR(25)) + ' WHERE Sire=''' + m.Sire + ''' AND SireID IS NULL--' + t.DogName + ' from ' + m.Sire,m.Sire,m.MatchScore,t.DogID,t.DogName,m.MatchScore
	FROM MinMatch m
	JOIN [sJRTCA].[Sire_TempMatch] t ON m.SireID=t.DogID AND m.MatchScore=t.MatchScore
	JOIN sAll.Dog d ON t.DogID=d.DogID
	JOIN (
		select d.dogname,d.dogid,e.entrycount
		from sall.dog d
		join sjrtca.entriesbydog e on d.dogid=e.dogid
		join sjrtca.maxentriesbydog m on e.dogname=m.dogname and e.entrycount=m.maxentries) AS e ON d.DogID=e.DogID
		
	where t.SireID<>t.DogID
	order by m.Sire;
GO

/****** Object:  StoredProcedure [sJRTCA].[spYouthCleanup]    Script Date: 12/12/2025 7:01:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [sJRTCA].[spYouthCleanup] AS
	select 'INSERT sall.owner (ownername) SELECT ''' + replace(dogname,'''','''''') + ''' UPDATE sall.dog SET ownerid=@@IDENTITY where dogname=''' + replace(dogname,'''','''''') + ''' and ownerid=17683',*
	from sall.dog
	where ownerid=17683 and dogname not like '%owned by%' and dogname not like '%with%' and dogname not like '%owed by%' and dogname not like '% owned %' and dogname not like '%,%';
GO


