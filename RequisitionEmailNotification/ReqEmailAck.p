{ud/GlbAlert.i &TableName = "ReqHead"}
/*
This procedure builds and sends an email to the concerned parties updating them on Req status. 
It also includes each Req Line and details pertaining to each item in an html table.

Also alerts purchasing department and, in high priority reqs, emails accounting.

The priority (Number01) system used by this is a simple customization on the Req Entry that adds a radio selection allowing a user
to specify the priority of their Requisition.

Still in WIP, so please test before using.
*/

ASSIGN
    SESSION:DATE-FORMAT = "dmy".

def var emailbody as char no-undo.

/** Build the generic email before we route... **/

/*Get the user record*/
find userfile where userfile.dcduserid = ReqHead.RequestorID no-lock no-error.

/*Create email*/
assign email-mime-header = {&HTML-Mime}.
assign email-from = 'alerts@acti.aero'.

/*DEBUG: TAKE THIS OUT WHEN WE ARE SURE ITS WORKIN OK.*/
assign email-cc = 'it@acti.aero'.

/* If the user email address doesn't exist....*/
IF userfile.emailaddress = ?  THEN DO:
	assign email-cc = 'it@acti.aero'.
	assign emailbody = emailbody + 'NOTICE: This user does not have an email address setup in Epicor....<BR>'.
END.

/*                  BEGIN              */
	
	
/* ROUTE: Just been (A)pproved... */

IF ReqHead.StatusType = 'A' THEN DO:
	assign email-to = userfile.emailaddress.
	assign email-cc = email-cc + ';purchasing@acti.aero'.
	assign email-subject = 'Your Requisition: #' + string(ReqHead.ReqNum) + ' has just been APPROVED.'.
	assign emailbody = emailbody + 'The requisition is now waiting for puchasing to order.: <BR><BR><HR>'.
	END.

/* ROUTE: Just been (O)rdered... */
	
ELSE IF ReqHead.StatusType = 'O' THEN DO:
	assign email-to = userfile.emailaddress.
	assign email-subject = 'Your Requisition: #' + string(ReqHead.ReqNum) + ' has just been ORDERED.'.
	assign emailbody = emailbody + 'Just in case you forgot, here are the details of your requisition: <BR><BR><HR>'.
	END.

/* ROUTE: Just been (R)ejected... */
	
ELSE IF ReqHead.StatusType = 'R' THEN DO:
	assign email-to = userfile.emailaddress.
	assign email-subject = 'Your Requisition: #' + string(ReqHead.ReqNum) + ' has just been REJECTED.'.
	assign emailbody = emailbody + 'Just in case you forgot, here are the details of your requisition: <BR><BR><HR>'.
	END.

ELSE IF ReqHead.StatusType = 'P' AND ReqHead.ReqActionID = 'INITPO' THEN DO:
	assign email-to = userfile.emailaddress.
	assign email-subject = 'Your Requisition: #' + string(ReqHead.ReqNum) + ' has just been SENT TO PURCHASING.'.
	assign emailbody = emailbody + 'Just in case you forgot, here are the details of your requisition: <BR><BR><HR>'.
	END.

/* ROUTE: Initial dispatch (P)ending... */

ELSE IF ReqHead.StatusType = 'P' AND ReqHead.ReqActionID <> 'INITPO' THEN DO:
	assign email-to = 'purchasing@acti.aero'.
	IF ReqHead.Number01 = 0 THEN DO:
		assign email-subject = '[No Priority]'.
	END.

	IF ReqHead.Number01 = 1 THEN DO:
		assign email-subject = '[Low Priority]'.
	END.

	IF ReqHead.Number01 = 2 THEN DO:
		assign email-subject = '[Medium Priority]'.
	END.

	IF ReqHead.Number01 = 3 THEN DO:
		assign email-subject  = '[HIGH PRIORITY]'.
		assign email-cc = email-cc + 
		';accounting@acti.aero'.
	END.

	IF ReqHead.Number01 = 4 THEN DO:
		assign email-subject = 'EMERGENCY PURCHASE ORDER: '.
		assign email-cc = email-cc +
		';accounting@acti.aero'.
		assign emailbody = emailbody + 
		'<b>THIS HAS BEEN MARKED AS AN EMERGENCY ORDER. PLEASE TAKE NECESSARY STEPS TO EXPEDITE PROCESSES.</b><BR><BR>'.
	END.
	
	assign emailbody = emailbody + '<HR>'.
		assign email-subject = email-subject + 
		'[Requisition] ' + userfile.Name + ' has dispatched requistion #' + string(ReqHead.ReqNum).
END.


/***********************************************************/

assign emailbody = emailbody
+ '<font face="Arial" size="2">'
+ '<b>Req Number: </b>' + string(ReqHead.ReqNum) + '<BR><BR>'
+ '<b>Dispatch Notes: </b><BR>'
+ string(ReqHead.Note) + '<BR>'
+ '<b>Req Comments: </b><BR>' 
+ string(ReqHead.CommentText) + '<BR><BR>'.

/*Column headings*/
assign emailbody = emailbody
+ '<table align="center" border="1" cellspacing="1" cellpadding="1" style="Font-family:Arial;font-size:10pt;" bordercolor="#CCCCCC">'
+ '<tr>'
+ '<th>Line</th>'
+ '<th>Part</th>'
+ '<th>Class</th>'
+ '<th>OrderQty</th>'
+ '<th>UnitCost</th>'
+ '<th>Total</th>'
+ '<th>Taxable</th>'
+ '<th>Description</th>'
+ '<th>Comments</th>'
+ '</tr>'.

/*Release detail*/

for each ReqDetail of ReqHead no-lock.
	assign emailbody = emailbody
	+ '<tr>'
	+ '<td align="center">' + string(ReqDetail.ReqLine) + '</td>'
	+ '<td align="center">' + string(ReqDetail.PartNum) + '</td>'
	+ '<td align="center">' + string(ReqDetail.Class) + '</td>'
	+ '<td align="center">' + string(ReqDetail.XOrderQty) + '</td>'
	+ '<td align="center">' + string(ReqDetail.UnitCost, '->>,>>9.99') + '</td>'
	+ '<td align="center">' + string(ReqDetail.UnitCost * ReqDetail.XOrderQty, '->>,>>9.99') + '</td>'
	+ '<td align="center">' + string(ReqDetail.Taxable) + '</td>'
	+ '<td align="center">' + string(ReqDetail.LineDesc,"x(100)") + '</td>'
	+ '<td align="center">' + string(ReqDetail.CommentText, "x(100)") + '</td>'
	+ '<td align="center">&nbsp;</td>'
	+ '</tr>'.
end.


assign emailbody = emailbody + '</table><BR>'.
assign emailbody = emailbody + '<br><br> This is a notice from a custom BAM on the ReqHead table, which calls \\Apollo\Epicor\Epicor905\BAM\ReqStatusAlert.p'.
assign email-text = emailbody.

SESSION:DATE-FORMAT = "mdy".
