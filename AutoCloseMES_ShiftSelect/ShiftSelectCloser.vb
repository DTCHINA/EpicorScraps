'//**************************************************
'// Custom VB.NET code for ShiftSelect
'// Created: 9/12/2011 2:55:46 PM
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


    '// ** Wizard Insert Location - Do Not Remove 'Begin/End Wizard Added Module Level Variables' Comments! ** 
    '// Begin Wizard Added Module Level Variables ** 
Private WithEvents txtShift As EpiTextBox
Private WithEvents btnOK As EpiButton

    '// End Wizard Added Module Level Variables ** 


    '// Add Custom Module Level Variables Here ** 



    Sub InitializeCustomCode() 


        '// ** Wizard Insert Location - Do not delete 'Begin/End Wizard Added Variable Intialization' lines ** 
        '// Begin Wizard Added Variable Intialization 

        '// End Wizard Added Variable Intialization 
        '// Begin Custom Method Calls 

        
        '// End Custom Method Calls 
    End Sub 



    Sub DestroyCustomCode() 


        '// ** Wizard Insert Location - Do not delete 'Begin/End Wizard Added Object Disposal' lines ** 
        '// Begin Wizard Added Object Disposal 

        '// End Wizard Added Object Disposal 
        '// Begin Custom Code Disposal 

        '// End Custom Code Disposal 
    End Sub 

Private Sub ShiftSelect_Load(ByVal sender As object, ByVal args As EventArgs) Handles ShiftSelect.Load
    '//
    '// Add Event Handler Code
    '//
    txtShift = CType(csm.GetNativeControlReference("521b37e5-fc02-4fec-b1f2-39989c016e45"), EpiTextBox) 
    btnOK = CType(csm.GetNativeControlReference("ba471f56-bb12-4c65-a829-0777546ca44e"), EpiButton)
    For Each ctl As Control In ShiftSelect.Controls
    If (ctl.Name = "btnOK") Then
    btnOK = ctl
    ElseIf (ctl.Name = "txtShift") Then
    txtShift = ctl
    End If
    
    Next
    
    End Sub

Private Sub txtShift_Enter(ByVal sender As Object, ByVal args As EventArgs) Handles txtShift.Enter
btnOK.Focus()
btnOK.PerformClick()
End Sub


End Module 
