  function setDivMinMaxSizes() {
    setMinMaxSize("main");
  }
  
  function setMinMaxSize(divName) {
    // you can edit the values of the following three lines
	//var divName = "main";
    var maxWidth = 1200;
	var minWidth = 990;
	
	/*** DO NOT MODIFY ANYTHING BELOW THIS LINE ***/

	var ns6 = document.getElementById && !document.all		
	var sizediv = ns6 ? document.getElementById(divName) : document.all[divName];

	if (parseInt(navigator.appVersion)>3) {
	 if (navigator.appName=="Netscape") {
	   winW = window.innerWidth - 16 ;
	 
	 } else if( document.documentElement && ( document.documentElement.clientWidth || document.documentElement.clientHeight ) ) {
       //IE 6+ in 'standards compliant mode'     	   
	   winW = document.documentElement.clientWidth - 20;
     
	 } else if( document.body && ( document.body.clientWidth || document.body.clientHeight ) ) {
        //IE 4 compatible
        winW = document.body.clientWidth - 20; 
     }
	 
      if (winW > maxWidth) { 
	    sizediv.style.width = maxWidth + "px"; 
	  } else if (winW < minWidth) { 
	    sizediv.style.width = minWidth + "px"; 
	  } else if (sizediv.style.width != "100%") {
	    sizediv.style.width = "100%";
	  }
	}
	/*** DO NOT MODIFY ANYTHING ABOVE THIS LINE ***/
  }
  
  
if (navigator.appName!="Netscape") {
	if (window.addEventListener) {
	  window.addEventListener("resize", setDivMinMaxSizes);
	  window.addEventListener("load", setDivMinMaxSizes);
	} else if (window.attachEvent) {
	  window.attachEvent("onresize", setDivMinMaxSizes);
	  window.attachEvent("onload", setDivMinMaxSizes);	
	}
}






 


 var ns6=document.getElementById&&!document.all

  
  function runIntroSequenceCheck() {  
    
    var myCookie = getCookie();
    
    if (myCookie < maxIntroViews || maxIntroViews == -1) {
    	// only set a cookie if there is a "max allowable views" value set
    	if (maxIntroViews > 0) {
      	  setCookie(myCookie, isPersistantCookie);
      	  
    	} else if (maxIntroViews == 0) {
	       
	         // cannot communicate with flash movie if viewing page on local machine due to security concerns
	         if (!window.location.href.indexOf("http")) {

	           return "skip";
	       
	         }
    	}

    } else {
       
         // cannot communicate with flash movie if viewing page on local machine due to security concerns
         if (!window.location.href.indexOf("http")) {
           return "skip";
         }
      
    } 
    //alert ("noskip");
    return "noskip";
    //setIntroMovieParams();     
  }
  
 function bookmark(){
  if (document.all) {
    if (window.location.href.indexOf("http")) {
      alert("You cannot bookmark a page on your local computer.");
    } else {
      window.external.AddFavorite(document.location.href,document.title)
    }
  } else {
    alert("Please select CTRL-D to bookmark this page");
  }
}

function makeHomePage() {
	if (document.all){
	  document.body.style.behavior='url(#default#homepage)';
      document.body.setHomePage(document.location);
	}
}



function getCookie() {
  var cookieName = document.location + "";
  cookieName = cookieName.replace(/index.htm/gi, "");
  var cookieName2 = cookieName + "index.htm";

  var cookieBox = document.cookie.split("; ");
  for (var i=0; i< cookieBox.length; i++) {
      var cookiePacket = cookieBox[i].split("=");
      if (cookieName == cookiePacket[0] || cookieName2 == cookiePacket[0]) {
        return unescape(cookiePacket[1]);
      }
  }
  return 0;
}



function setCookie(myCookieState, isPersistant) {
  if (!myCookieState) {
    myCookieState = 0;
  }
  myCookieState++;
  myCookieInfo = document.location + "=" + myCookieState+ "; ";

  if (isPersistant == 1) {
    cookieExpiration = new Date();
    cookieExpiration.setFullYear(cookieExpiration.getFullYear() + 1);
    myCookieInfo = myCookieInfo + "expires="+cookieExpiration.toUTCString()+"; ";
  }
  document.cookie = myCookieInfo;
}
/*
Live Date Script- 
© Dynamic Drive (www.dynamicdrive.com)
For full source code, installation instructions, 100's more DHTML scripts, and Terms Of Use,
visit http://www.dynamicdrive.com
*/


var dayarray=new Array("Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday")
var montharray=new Array("January","February","March","April","May","June","July","August","September","October","November","December")

function getthedate(){
var mydate=new Date()
var year=mydate.getYear()
if (year < 1000)
year+=1900
var day=mydate.getDay()
var month=mydate.getMonth()
var daym=mydate.getDate()
if (daym<10)
daym="0"+daym
var hours=mydate.getHours()
var minutes=mydate.getMinutes()
var seconds=mydate.getSeconds()
var dn="AM"
if (hours>=12)
dn="PM"
if (hours>12){
hours=hours-12
}
if (hours==0)
hours=12
if (minutes<=9)
minutes="0"+minutes
if (seconds<=9)
seconds="0"+seconds
//change font size here
var cdate="<font face='Tahoma'>"+dayarray[day]+", "+montharray[month]+" "+daym+", "+year+" "+hours+":"+minutes+":"+seconds+" "+dn
+"</font>"
if (document.all)
document.all.clock.innerHTML=cdate
else if (document.getElementById)
document.getElementById("clock").innerHTML=cdate
else
document.write(cdate)
}
if (!document.all&&!document.getElementById)
getthedate()
function goforit(){
if (document.all||document.getElementById)
setInterval("getthedate()",1000)
}


function addEvent(obj, type, fn) {
	if (obj.addEventListener) {
		obj.addEventListener( type, fn, false );
	} else if (obj.attachEvent) {
		obj["e"+type+fn] = fn;
		obj[type+fn] = function() { obj["e"+type+fn]( window.event ); }
		obj.attachEvent( "on"+type, obj[type+fn] );
	}
}


//addEvent(window,'load',setupEditor);
addEvent(window,'load',goforit);

