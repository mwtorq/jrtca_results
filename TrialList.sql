SELECT [TrialListID]
      ,[Year]
      ,[Trial]
      ,[TrialName]
      ,[StartDate]
      ,[EndDate]
      ,[TrialResultFilePath]
      ,[Loaded]
      ,[Chairperson]
      ,[LocationCity]
      ,[LocationState]
      ,[JRTCA]
      ,[CreateUser]
      ,[CreateDateTime]
  FROM [TrialResults].[sResults].[TrialList]
  --WHERE StartDate LIKE '%01-01%'
  --WHERE (TrialName LIKE '%MOE%' OR TrialName LIKE '%Earthdogs%')
  ORDER BY StartDate

  --update [TrialResults].[sResults].[TrialList] set trialname='2002 Missouri Earthdogs Memorial Day Bash' WHERE triallistid=1691
  --update [TrialResults].[sResults].[TrialList] set trialname='2003 Missouri Earthdogs Memorial Day Bash' WHERE triallistid=1692
  --update [TrialResults].[sResults].[TrialList] set trialname='2009 Missouri Earthdogs Memorial Day Bash' WHERE triallistid=1695
  --update [TrialResults].[sResults].[TrialList] set trialname='2013 Missouri Earthdogs Memorial Day Bash' WHERE triallistid=1697
  --update [TrialResults].[sResults].[TrialList] set trialname='2015 Missouri Earthdogs Memorial Day Bash' WHERE triallistid=1698
  --delete [TrialResults].[sResults].[TrialList]