{ud/GlbAlert.i &TableName = "OrderHed"}
/*
This procedure builds and sends an email to the email address of the order entry person .
*/
ASSIGN
    SESSION:DATE-FORMAT = "dmy".

def var emailbody as char no-undo.

/*Get the user record*/
find userfile where userfile.dcduserid = orderhed.entryperson no-lock no-error.

/*Get Customer/ShipTo Record*/
find customer where orderhed.custnum = customer.custnum no-lock no-error.
find shipto where orderhed.custnum = shipto.custnum and orderhed.shiptonum = shipto.shiptonum no-lock no-error.


/*Create email*/
assign email-from = 'alerts@acti.aero'.
assign email-to = 'orders@acti.aero'.

IF userfile.emailaddress = ?  THEN DO:
	assign email-cc = 'it@acti.aero'.
	assign emailbody = emailbody + 'User does not have email address! Please update user file in Epicor!.<BR>'.
END.
ELSE DO:
	assign email-cc = userfile.emailaddress + ';it@acti.aero'.
END.

assign email-subject = '[sales order] ' + orderhed.entryperson + ' created an order for ' + customer.name.
assign email-mime-header = {&HTML-Mime}.

assign emailbody = emailbody
+ '<BR>'
+ '<font face="Arial" size="2">A Sales Order has been marked Ready To Process.<BR>'
+ '<b>Order Number: </b>' + string(orderhed.ordernum) + '<BR>'
+ '<b>PO Number:</b> '
+ string(orderhed.ponum) + ', dated ' + string(orderhed.orderdate) + '.<BR>'
+ '<b>TermsCode:</b>' + string(orderhed.termscode) + '<BR>'
+ '<b>Customer: </b>' + string(customer.custid) + '<BR>'.

/*Now get the Bill To customer record.*/
find customer where orderhed.btcustnum = customer.custnum no-lock no-error.

assign emailbody = emailbody
+ '<b>Bill To: </b>' + string(customer.custid) + '<BR>'
+ '<b>Ship To:</b> ' + string(shipto.name) + '<BR>'
+ ' <b>Delivery Address:</b> <BR>' 
+ string(shipto.address1) + ', <BR>'
+ string(shipto.address2) + ', <BR>'
+ string(shipto.address3) + ', <BR>'
+ string(shipto.city) + ', <BR>'
+ string(shipto.state) + ', <BR>'
+ string(shipto.zip) + ','
+ '<BR><BR>'.


/*Column headings*/
assign emailbody = emailbody
+ '<table border="1" cellspacing="0" cellpadding="0" style="Font-family:Arial;font-size:10pt;" bordercolor="#CCCCCC">'
+ '<tr>'
+ '<th>Line/Rel</th>'
+ '<th>Part</th>'
+ '<th>Description</th>'
+ '<th>Quantity</th>'
+ '<th>Price Each</th>'
+ '<th>Total Value</th>'
+ '<th>Need By Date</th>'
+ '</tr>'.

/*Release detail*/
for each orderdtl of orderhed no-lock.
    for each orderrel of orderdtl no-lock.
        for each partwhse of orderrel where orderrel.partnum = partwhse.partnum and orderrel.warehousecode = partwhse.warehousecode no-lock. 
            assign emailbody = emailbody
            + '<tr>'
            + '<td>' + string(orderrel.orderline) + '/' + string(orderrel.orderrelnum) + '</td>'
            + '<td>' + string(orderdtl.partnum) + '</td>'
            + '<td>' + string(orderdtl.linedesc,"x(100)") + '</td>'
            + '<td>' + string(orderrel.sellingreqqty) + '</td>'
            + '<td>' + string(orderdtl.docunitprice, '->>,>>9.99') + '</td>'
            + '<td>' + string(orderdtl.docunitprice * orderrel.sellingreqqty, '->>,>>9.99') + '</td>'
            + '<td>' + string(orderrel.needbydate) + '</td>'
			+ '<td>&nbsp;</td>'
			+ '</tr>'.
        end.
    end.
end.

assign emailbody = emailbody + '</table><BR>'.
assign emailbody = emailbody + '<br><br> This is a notice from a custom BAM on the OrderHed table, which calls \\Apollo\Epicor\Epicor905\BAM\SalesOrderAlert.p'.
assign email-text = emailbody.

SESSION:DATE-FORMAT = "mdy".
