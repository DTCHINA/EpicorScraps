'//**************************************************
'// Custom VB.NET code for MESMenu
'// Created: 8/12/2011 11:48:29 AM
'//**************************************************
Imports System
Imports System.Data
Imports System.Diagnostics
Imports System.Windows.Forms
Imports System.ComponentModel
Imports Microsoft.VisualBasic
Imports Epicor.Mfg.UI
Imports Epicor.Mfg.UI.FrameWork
Imports Epicor.Mfg.UI.ExtendedProps
Imports Epicor.Mfg.UI.FormFunctions
Imports Epicor.Mfg.UI.Customization
Imports Epicor.Mfg.UI.Adapters
Imports Epicor.Mfg.UI.Searches
Imports Epicor.Mfg.BO


Module Script 

	' Lunch Status codes
	' 0  : No lunch taken yet, ie Number01 & Number02 = 0
	' 1  : Out at lunch, ie Number01 > 0 & Number02 = 0
	' 2  : Lunch taken, ie Number01 > 0 & Number02 > 0
	' 3  : Error Condition, Number01 = 0 & Number02 > 0
	Private Const NO_LUNCH As Integer = 0
	Private Const AT_LUNCH As Integer = 1
	Private Const TAKEN_LUNCH As Integer = 2
	Private Const LUNCH_ERROR As Integer = 3

	
	Dim jobgrid As EpiUltraGrid
	Private WithEvents edvLaborHed As EpiDataView
	
	Sub InitializeCustomCode() 
		Script.edvLaborHed = CType(Script.oTrans.EpiDataViews("LaborHed"),EpiDataView)
		AddHandler Script.edvLaborHed.EpiViewNotification, AddressOf Script.edvLaborHed_EpiViewNotification
		AddHandler Script.epiButtonC1.Click, AddressOf Script.epiButtonC1_Click 'LOB Button
		AddHandler Script.epiButtonC2.Click, AddressOf Script.epiButtonC2_Click 'LunchOUT Button
		AddHandler Script.epiButtonC3.Click, AddressOf Script.epiButtonC3_Click 'LunchIN Button
		AddHandler Script.MESControl_Row.EpiRowChanged, AddressOf Script.MESControl_AfterRowChange
		ClearLunchButtons()


		jobgrid = ctype(csm.GetNativeControlReference("a9cf2b4f-03f2-499e-9744-c311af7f8172"),EpiUltraGrid)
		jobgrid.Enabled = true
		jobgrid.ReadOnly = false
		jobgrid.IsEpiReadOnly = false
		jobgrid.EpiEnabledControl = true	
	End Sub 

		
	'********************* update_comp_message **********************
	'
	'		Updates message bar at the bottom of the MES form,
	'		this is set by a control panel in the Epicor HR 
	'		folder.
	'
	'***********************************************************
		
	Sub update_comp_message() 
		Dim compAdapt As CompanyAdapter = New CompanyAdapter (MESMENU)
		Dim txtIdBox As EpitextBox = ctype(csm.GetNativeControlReference("fca2b60c-95cf-40b4-adc0-c168fc3a43fc"),EpitextBox)
		compAdapt.BOConnect ()
		dim company as string
		company = "ACT"
		compAdapt.GetByID(company)
		compAdapt.CompanyData.Tables("Company").Rows(0).BeginEdit()
		txtEpiCustom2.Text = compAdapt.CompanyData.Tables("Company").Rows(0)("Character02")
		Dim newFont as New System.Drawing.Font("Tahoma",18,System.Drawing.FontStyle.Bold)
		txtEpiCustom2.Font = newFont
		compAdapt.CompanyData.Tables("Company").Rows(0).EndEdit()
		compAdapt.Update( )
		txtIdBox.Focus()
		compAdapt.Dispose( )
		jobgrid.Enabled = true
		jobgrid.ReadOnly = false
		jobgrid.IsEpiReadOnly = false
		jobgrid.EpiEnabledControl = true	
	End Sub

	'********************* Run_The_LOB  ************************
	'		Calls the BAQ Report Form ACT-LOBFVPrices
	'***********************************************************
	Sub Run_The_LOB()
		ProcessCaller.LaunchForm(oTrans, "UDLOBPR")
	End Sub
	
	
	'********************* Lunch_Punch_Out / In *********************
	'
	'		Part of the ACTI lunch tracking system. 
	'		Sets the LaborHed.ActLunchInTime/Out of the current labor
	'		record to the current date/time. This is to circumvent
	'		the need to clock out of jobs before clocking out on MES
	'		for lunch time tracking.
	'
	' TODO: I should really look into using LaborHed.LunchInTime, .LunchOutTime, and .LunchStatus instead of Number01/02
	'NOTE:
	'LunchStatus: An internal control byte used by Labor Collection when the system is configured not to take out lunch automatically 
	'(JCSyst.AutoLunch = N). It is used determine if what to do when the "Lunch" button is pressed. The possible values are 
	'"N" - No lunch, "O" - Out to Lunch, "R" - Returned from lunch.

	'***********************************************************
	Sub Lunch_Punch_Out()
		Dim LogoutBtn As Epibutton = ctype(csm.GetNativeControlReference("a2f6e795-4ab3-4121-bce4-e1d5f0881b0a"),Epibutton)
		edvLaborHed.dataView(edvLaborHed.Row).BeginEdit()
		edvLaborHed.dataView(edvLaborHed.Row)("ActLunchOutTime") = new TimeSpan(DateTime.Now.Hour, DateTime.Now.Minute, 0).TotalHours ' So we look like 6.5 for 06:30
		edvLaborHed.dataView(edvLaborHed.Row)("LunchStatus") = "O"
		edvLaborHed.dataView(edvLaborHed.Row).EndEdit()
		edvLaborHed.Notify(New EpiNotifyArgs(oTrans, edvLaborHed.Row, edvLaborHed.Column))
		oTrans.Update()
		LogoutBtn.PerformClick()
	End Sub
	
	Sub Lunch_Punch_In() 'Back from lunch
		Dim LogoutBtn As Epibutton = ctype(csm.GetNativeControlReference("a2f6e795-4ab3-4121-bce4-e1d5f0881b0a"),Epibutton)
		edvLaborHed.dataView(edvLaborHed.Row).BeginEdit()
		edvLaborHed.dataView(edvLaborHed.Row)("ActLunchInTime") = new TimeSpan(DateTime.Now.Hour, DateTime.Now.Minute, 0).TotalHours
		edvLaborHed.dataView(edvLaborHed.Row)("LunchStatus") = "R"
		edvLaborHed.dataView(edvLaborHed.Row).EndEdit()
        edvLaborHed.Notify(New EpiNotifyArgs(oTrans, edvLaborHed.Row, edvLaborHed.Column))
		oTrans.Update()
		LogoutBtn.PerformClick()
	End Sub
		
		
	Private Function Lunch_Status() As Integer
		Dim L_Leave As string = edvLaborHed.dataView(edvLaborHed.Row)("LunchStatus")
		If (L_Leave = "") Then 'zero, essentially
			Return NO_LUNCH
		End If
		'User Is "Out to lunch"
		If (L_Leave = "O") Then
			Return AT_LUNCH
		End If
		'User has already taken lunch
		If (L_Leave = "R") Then
			Return TAKEN_LUNCH
		End If
	End Function
		
	Sub ClearLunchButtons()
		Dim LunchOut As Epibutton = ctype(csm.GetNativeControlReference("d0257385-069c-4c12-a202-2cd38e544168"),Epibutton) 
		Dim LunchIN As Epibutton = ctype(csm.GetNativeControlReference("ed78b75d-bf3e-49cd-9e40-1d89db578816"),Epibutton) 
		LunchOut.Enabled = FALSE
		LunchIn.Enabled = FALSE
	End Sub

	Sub SetLunchButtons() 
		Dim CurrentStatus As Integer 
		'gotolunch
		Dim LunchOut As Epibutton = ctype(csm.GetNativeControlReference("d0257385-069c-4c12-a202-2cd38e544168"),Epibutton) 
		'backfromlunch
		Dim LunchIN As Epibutton = ctype(csm.GetNativeControlReference("ed78b75d-bf3e-49cd-9e40-1d89db578816"),Epibutton) 
		
		CurrentStatus= Lunch_Status()
		
		If (CurrentStatus = NO_LUNCH) Then
				'do nothing
				LunchOut.Enabled = TRUE
				LunchIn.Enabled = FALSE
		End If
		If (CurrentStatus = TAKEN_LUNCH) Then
				LunchOut.Enabled = FALSE
				LunchIn.Enabled = FALSE
		End If
		If (CurrentStatus = AT_LUNCH) Then
				LunchOut.Enabled = FALSE
				LunchIn.Enabled = TRUE
		End If


	End Sub
		

	Sub DestroyCustomCode() 
		RemoveHandler Script.edvLaborHed.EpiViewNotification, AddressOf Script.edvLaborHed_EpiViewNotification
		Script.edvLaborHed = Nothing
		RemoveHandler Script.epiButtonC1.Click, AddressOf Script.epiButtonC1_Click 'LOB
		RemoveHandler Script.epiButtonC2.Click, AddressOf Script.epiButtonC2_Click 'LunchOUT
		RemoveHandler Script.epiButtonC3.Click, AddressOf Script.epiButtonC3_Click 'LunchIN
		RemoveHandler Script.MESMenu.Keypress, AddressOf Script.Form1_Keypress
		RemoveHandler Script.MESControl_Row.EpiRowChanged, AddressOf Script.MESControl_AfterRowChange
	End Sub 

	Private Sub edvLaborHed_EpiViewNotification(ByVal view As EpiDataView, ByVal args As EpiNotifyArgs)
		If (args.NotifyType = EpiTransaction.NotifyType.Initialize) Then
			If (args.Row > -1) Then	
				edvLaborHed.dataView(edvLaborHed.Row).BeginEdit()
				edvLaborHed.dataView(edvLaborHed.Row)("Character01") = System.Environment.Machinename.ToString
		
				'Here's a bit of a hack:
				'When a user logs into a shift (Creates a LaborHed record) their Lunch time is preset. If
				'a user does NOT use our LunchOut/In buttons then it gives the employee the default shift lunch.
				'Which is why we zero them out, so we can actually see when someone skips lunch.
				if (edvLaborHed.dataView(edvLaborHed.Row)("LunchStatus") = "N") Then
					edvLaborHed.dataView(edvLaborHed.Row)("ActLunchInTime") = 0 
					edvLaborHed.dataView(edvLaborHed.Row)("ActLunchOutTime") = 0
					End If
				edvLaborHed.dataView(edvLaborHed.Row).EndEdit()
				oTrans.Update()
	
				Dim LunchOut As Epibutton = ctype(csm.GetNativeControlReference("d0257385-069c-4c12-a202-2cd38e544168"),Epibutton) 
				Dim LunchIN As Epibutton = ctype(csm.GetNativeControlReference("ed78b75d-bf3e-49cd-9e40-1d89db578816"),Epibutton) 
				
				LunchOut.Enabled = False
				LunchIN.Enabled = False

				SetLunchButtons()
			End If
			
				
		End If
	End Sub


	Private Sub MESMenu_Load(ByVal sender As object, ByVal args As EventArgs) Handles MESMenu.Load
		picEpiCustom1.Image = System.Drawing.Image.FromFile("\\APOLLO\Epicor905\acti.jpg") ' Company Logo
		update_comp_message()  '	Update the Company message on load
		Dim LogoutBtn As Epibutton = ctype(csm.GetNativeControlReference("d69f285b-eee4-48fd-a6fa-174583fdfbd9"),Epibutton)
		Dim LunchOutBtn As Epibutton = ctype(csm.GetNativeControlReference("d0257385-069c-4c12-a202-2cd38e544168"),Epibutton) 
		Dim LunchINBtn As Epibutton = ctype(csm.GetNativeControlReference("ed78b75d-bf3e-49cd-9e40-1d89db578816"),Epibutton) 

		LogoutBtn.UseAppStyling = False
		LunchOutBtn.UseAppStyling = False
		LunchINBtn.UseAppStyling = False

		LogoutBtn.BackColor = System.Drawing.Color.Red ' Is this necessary?
		LunchOutBtn.BackColor = System.Drawing.Color.LightBlue
		LunchINBtn.BackColor = System.Drawing.Color.Orange
	    MESMenu.Keypreview = true 	
		'MESMenu.ActiveControl = txtIDBox
	End Sub


	'********************* Form1_KeyPress **********************
	'
	'		Catch all keypresses, if it's one of ours handle it.
	'
	'***********************************************************
	Private Sub Form1_KeyPress(ByVal sender As Object, ByVal e As System.Windows.Forms.KeyPressEventArgs) Handles MESMenu.KeyPress
		Dim txtIdBox As EpitextBox = ctype(csm.GetNativeControlReference("fca2b60c-95cf-40b4-adc0-c168fc3a43fc"),EpitextBox)
		Dim LogoutBtn As Epibutton = ctype(csm.GetNativeControlReference("a2f6e795-4ab3-4121-bce4-e1d5f0881b0a"),Epibutton)
		Dim ClockOutBtn As EpiButton = ctype(csm.GetNativeControlReference("1c55d195-3d9f-4883-8151-3fc15a3d7b8d"),EpiButton)
	
		'Watch for keypresses. If it looks like part of a badge scan, handle it.
		if (txtIdBox.Focused = False) 'This is no good, means we can't login/out if the idbox is focused.
			Select Case e.KeyChar
				Case "1","2","3","4","5","6","7","8","9","0"  'sigh...
					txtIdBox.Select()
					SendKeys.Send(Convert.ToString(e.KeyChar))
					e.Handled() = TRUE
				Case "L"
					LogoutBtn.PerformClick()
					e.Handled() = TRUE
				Case "O"
					txtIdBox.Focus() ' Why is this here again...?
					ClockOutBtn.PerformClick()
					e.Handled() = TRUE
			End Select
		End if 

	End Sub

	
	Private Sub MESControl_AfterFieldChange(ByVal sender As object, ByVal args As DataColumnChangeEventArgs) Handles MESControl_Column.ColumnChanged
		jobgrid.Enabled = true
		jobgrid.ReadOnly = false
		Select Case args.Column.ColumnName
			Case "LoggedIn"
	               Dim edvMESControl as epidataview = CType(oTrans.EpiDataViews("MESControl"), EpiDataView)
	               Dim edvEmpBasic as epidataview = CType(oTrans.EpiDataViews("EmpBasic"), EpiDataView)
		   
			   'TODO: if logged in date is yesterday, flag it with messagebox or something
	               Dim logd as boolean = edvMESControl.dataView(edvMESControl.Row)("LoggedIn")
	                 If (logd = false) then 'Logged Out
						ClearLunchButtons()
						edvEmpBasic.dataview(edvEmpBasic.Row)("EmpID") = "" 'If we dont clear this, MyHours will report last logged in emp while no user is logged in.
					End If
	                 
			Case "EmployeeID"
				update_comp_message() 'Update on each employee scan, so we make sure it's up to date!
			Case Else
				'nothing...
		End Select
	
	End Sub
	

	'******************** Button Event Handling *********************
	
	Private Sub epiButtonC1_Click(ByVal sender As Object, ByVal args As System.EventArgs)
		ProcessCaller.LaunchForm(oTrans, "UDLOBPR")
	End Sub

	Private Sub epiButtonC2_Click(ByVal sender As Object, ByVal args As System.EventArgs)
		Lunch_Punch_Out()
	End Sub

	Private Sub epiButtonC3_Click(ByVal sender As Object, ByVal args As System.EventArgs)
		Lunch_Punch_In()
	End Sub


	Private Sub MESControl_AfterRowChange(ByVal args As EpiRowChangedArgs)
		' ** Argument Properties and Uses **
		' args.CurrentView.dataView(args.CurrentRow)("FieldName")
		' args.LastRow, args.CurrentRow, args.CurrentView
		' Add Event Handler Code
		Dim LunchOut As Epibutton = ctype(csm.GetNativeControlReference("d0257385-069c-4c12-a202-2cd38e544168"),Epibutton) 
		Dim LunchIN As Epibutton = ctype(csm.GetNativeControlReference("ed78b75d-bf3e-49cd-9e40-1d89db578816"),Epibutton) 
		Dim DEBUGBOX As EpiTextBox = ctype(csm.GetNativeControlReference("87fa30f4-0ef7-4387-a5cb-d1595b973600"),EpiTextBox)
		LunchOut.Enabled = False
		LunchIN.Enabled = False
		SetLunchButtons() 'huh?
		jobgrid.Enabled = true
		jobgrid.ReadOnly = false
		jobgrid.IsEpiReadOnly = false
		jobgrid.EpiEnabledControl = true	
	End Sub
End Module 
