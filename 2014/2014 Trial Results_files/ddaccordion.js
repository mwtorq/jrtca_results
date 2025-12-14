//Accordion Content script: By Dynamic Drive, at http://www.dynamicdrive.com
//Created: Jan 7th, 08'

var ddaccordion={
	
	contentclassname:{}, //object to store corresponding contentclass name based on headerclass

	expandone:function(headerclass, selected){ //PUBLIC function to expand a particular header
		this.toggleone(headerclass, selected, "expand")
	},

	collapseone:function(headerclass, selected){ //PUBLIC function to collapse a particular header
		this.toggleone(headerclass, selected, "collapse")
	},

	expandall:function(headerclass){ //PUBLIC function to expand all headers based on their shared CSS classname
		var _$headers=_$('.'+headerclass)
		_$('.'+this.contentclassname[headerclass]+':hidden').each(function(){
			_$headers.eq(parseInt(_$(this).attr('contentindex'))).click()
		})
	},

	collapseall:function(headerclass){ //PUBLIC function to collapse all headers based on their shared CSS classname
		var _$headers=_$('.'+headerclass)
		_$('.'+this.contentclassname[headerclass]+':visible').each(function(){
			_$headers.eq(parseInt(_$(this).attr('contentindex'))).click()
		})
	},

	toggleone:function(headerclass, selected, optstate){ //PUBLIC function to expand/ collapse a particular header
		var _$targetHeader=_$('.'+headerclass).eq(selected)
		var _$subcontent=_$('.'+this.contentclassname[headerclass]).eq(selected)
		if (typeof optstate=="undefined" || optstate=="expand" && _$subcontent.is(":hidden") || optstate=="collapse" && _$subcontent.is(":visible"))
			_$targetHeader.click()
	},

	expandit:function(_$targetHeader, _$targetContent, config){
		_$targetContent.slideDown(config.animatespeed)
		this.transformHeader(_$targetHeader, config, "expand")
	},

	collapseit:function(_$targetHeader, _$targetContent, config){
		_$targetContent.slideUp(config.animatespeed)
		this.transformHeader(_$targetHeader, config, "collapse")
	},

	transformHeader:function(_$targetHeader, config, state){
		_$targetHeader.addClass((state=="expand")? config.cssclass.expand : config.cssclass.collapse) //alternate btw "expand" and "collapse" CSS classes
		.removeClass((state=="expand")? config.cssclass.collapse : config.cssclass.expand)
		if (config.htmlsetting.location=='src'){ //Change header image (assuming header is an image)?
			_$targetHeader=(_$targetHeader.is("img"))? _$targetHeader : _$targetHeader.find('img').eq(0) //Set target to either header itself, or first image within header
			_$targetHeader.attr('src', (state=="expand")? config.htmlsetting.expand : config.htmlsetting.collapse) //change header image
		}
		else if (config.htmlsetting.location=="prefix") //if change "prefix" HTML, locate dynamically added ".accordprefix" span tag and change it
			_$targetHeader.find('.accordprefix').html((state=="expand")? config.htmlsetting.expand : config.htmlsetting.collapse)
		else if (config.htmlsetting.location=="suffix")
			_$targetHeader.find('.accordsuffix').html((state=="expand")? config.htmlsetting.expand : config.htmlsetting.collapse)
	},

	getCookie:function(Name){ 
		var re=new RegExp(Name+"=[^;]+", "i") //construct RE to search for target name/value pair
		if (document.cookie.match(re)) //if cookie found
			return document.cookie.match(re)[0].split("=")[1] //return its value
		return null
	},

	setCookie:function(name, value){
		document.cookie = name + "=" + value
	},

	init:function(config){
	document.write('<style type="text/css">\n')
	document.write('.'+config.contentclass+'{display: none}\n') //generate CSS to hide contents
	document.write('<\/style>')
	
	_$(document).ready(function(){

		ddaccordion.contentclassname[config.headerclass]=config.contentclass //remember contentclass name based on headerclass
		config.cssclass={collapse: config.toggleclass[0], expand: config.toggleclass[1]} //store expand and contract CSS classes as object properties
		config.htmlsetting={location: config.togglehtml[0], collapse: config.togglehtml[1], expand: config.togglehtml[2]} //store HTML settings as object properties
		var lastexpanded={} //object to hold reference to last expanded header and content (jquery objects)
		var expandedindices=(config.persiststate)? ddaccordion.getCookie(config.headerclass) : config.defaultexpanded
		expandedindices=(typeof expandedindices=='string')? expandedindices.replace(/c/ig, '').split(',') : config.defaultexpanded //test for valid cookie ('string'), otherwise (null, or 1st page load), default to defaultexpanded setting
		var _$subcontents=_$('.'+config["contentclass"])
		if (config["collapseprev"] && expandedindices.length>1)
			expandedindices=[expandedindices.pop()] //return last array element as an array (for sake of jQuery.inArray())
		
		
		_$('.'+config["headerclass"]).each(function(index){ //loop through all headers
			if (/(prefix)|(suffix)/i.test(config.htmlsetting.location) && _$(this).html()!=""){ //add a SPAN element to header depending on user setting and if header is a container tag
				_$('<span class="accordprefix"></span>').prependTo(this)
				_$('<span class="accordsuffix"></span>').appendTo(this)
			}
			_$(this).attr('headerindex', index+'h') //store position of this header relative to its peers
			_$subcontents.eq(index).attr('contentindex', index+'c') //store position of this content relative to its peers
			var _$subcontent=_$subcontents.eq(index)
			if (jQuery.inArray(index, expandedindices)!=-1){ //check for headers that should be expanded automatically
				if (config.animatedefault==false)
					_$subcontent.show()
				ddaccordion.expandit(_$(this), _$subcontent, config)
				lastexpanded={_$header:_$(this), _$content:_$subcontent}
			}  //end check
			else{
				_$subcontent.hide()
				ddaccordion.transformHeader(_$(this), config, "collapse")
			}
		})
		_$('.'+config["headerclass"]).click(function(){ //assign behavior when headers are clicked on
				var _$subcontent=_$subcontents.eq(parseInt(_$(this).attr('headerindex'))) //get subcontent that should be expanded/collapsed
				if (_$subcontent.css('display')=="none"){
					ddaccordion.expandit(_$(this), _$subcontent, config)
					if (config["collapseprev"] && lastexpanded._$header && _$(this).get(0)!=lastexpanded._$header.get(0)){ //collapse previous content?
						ddaccordion.collapseit(lastexpanded._$header, lastexpanded._$content, config)
					}
					lastexpanded={_$header:_$(this), _$content:_$subcontent}
				}
				else{
					ddaccordion.collapseit(_$(this), _$subcontent, config)
				}
				return false
 	})
		_$(window).bind('unload', function(){ //clean up and persist on page unload
			_$('.'+config["headerclass"]).unbind('click')
			var expandedindices=[]
			_$('.'+config["contentclass"]+":visible").each(function(index){ //get indices of expanded headers
				expandedindices.push(_$(this).attr('contentindex'))
			})
			if (config.persiststate==true){ //persist state?
				expandedindices=(expandedindices.length==0)? '-1c' : expandedindices //No contents expanded, indicate that with dummy '-1c' value?
				ddaccordion.setCookie(config.headerclass, expandedindices)
			}
		})
	})
	}
}