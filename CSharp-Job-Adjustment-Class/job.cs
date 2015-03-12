using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using Epicor.Mfg.Core;
using Epicor.Mfg.BO;
using Epicor.Mfg.IF;
using Epicor.Mfg.Common;


namespace SwiftScan
{
    class Job
    {
        public Session Session { get; set; }
        public string Jobnumber { get; set; }

        JobStatus _job;
        JobStatusDataSet _jobDs;

        public Job(Session getSession, string jobnum)
        {
            this.Session = getSession;
            this.Jobnumber = jobnum;
            this.loadjob(jobnum);
        }

        public Job(string jobnum)
        {
            //default session
            this.Jobnumber = jobnum;
            this.Session = Program.SConnPool;
            this.loadjob(jobnum);
        }

        private void loadjob(string jobnum)
        {
            try
            {
                _job = new JobStatus(this.Session.ConnectionPool);
                    _jobDs = this._job.GetByID(this.Jobnumber);
            }
            catch
            {
               // MessageBox.Show("[Job.LoadJob()]" + e.Message + "\n" + e.InnerException.Message);
                throw;
            }
        }

        public string GetField(string fieldname)
        {
            ///<summary>
            ///Returns the field value for JobHead.fieldname
            ///</summary>
            return this._jobDs.JobHead[0][fieldname].ToString();
        }


        public bool OpenJob()
        {
            var jobClose = new JobClosing(this.Session.ConnectionPool);
            var jobCloseDs = new JobClosingDataSet();
            string msg="";
            string allmsg="";
            bool req;
            
            jobClose.GetNewJobClosing(jobCloseDs);

            try
            {
                jobClose.OnChangeJobNum(this.Jobnumber, jobCloseDs, out msg);
                allmsg += msg;


                jobCloseDs.JobClosing.Rows[0]["JobComplete"] = "False";
                jobCloseDs.JobClosing.Rows[0]["JobClosed"] = "False";
                jobClose.PreCloseJob(jobCloseDs,out req);
                jobClose.CloseJob(jobCloseDs, out msg);

                //add logging
            }
            catch(Exception exp)
            {
                MessageBox.Show(exp.Message);
            }
            
           
            return true;
        }


        public void Close(DateTime ClosingDate, out string message)
        {
            //Job Closing Routine.

            bool requserinput;

            var jobClose = new JobClosing(this.Session.ConnectionPool);
            var jobCloseDs = new JobClosingDataSet();

            jobClose.GetNewJobClosing(jobCloseDs);

            try
            {
                string msg = "";
                string allmsg = "";
                jobClose.OnChangeJobNum(this.Jobnumber, jobCloseDs, out msg); allmsg += msg;
                jobCloseDs.JobClosing.Rows[0]["JobClosed"] = "True";
                jobCloseDs.JobClosing.Rows[0]["QuantityContinue"] = "True";
                jobCloseDs.JobClosing.Rows[0]["JobComplete"] = "True";

                jobCloseDs.JobClosing.Rows[0]["JobCompletionDate"] = ClosingDate.ToString();
                jobCloseDs.JobClosing.Rows[0]["ClosedDate"] = ClosingDate.ToString();

                jobCloseDs.JobClosing.Rows[0]["RowMod"] = "U";

                jobClose.PreCloseJob(jobCloseDs, out requserinput);
                if (requserinput == true)
                    allmsg += "Require UserInput!";

                jobClose.CloseJob(jobCloseDs, out msg); allmsg += msg;
                message = allmsg;
            }

            catch (Exception joberr)
            {
                Log.LogThis(joberr.Message, eloglevel.error);
                throw;
            }


        }

        public JobStatusDataSet GetStatusDs()
        {
            return this._jobDs;
        }

        public JobOperListDataSet GetOperationListDs()
        {
            var jobOpSearch = new JobOperSearch(this.Session.ConnectionPool);

            bool pgs;
            try
            {
                JobOperListDataSet jobOperList = jobOpSearch.GetList("JobNum = \'" + this.Jobnumber + "\'", 0, 0, out pgs);
                return jobOperList;
            }
            catch
            {
                return null;
            }
        }

        public NonConfListDataSet GetNonConfListDS()
        {
            NonConf JobNonConf;
            NonConfListDataSet JobNonConfList;
            bool pgs;

            JobNonConf = new NonConf(this.Session.ConnectionPool);
            JobNonConfList = new NonConfListDataSet();

            try
            {
                JobNonConfList = JobNonConf.GetList("JobNum = \'" + this.Jobnumber + "\'", 0, 0, out pgs);
                return JobNonConfList;
            }
            catch
            {
                return null;
            }
        }

        public LaborDtlListDataSet GetLaborListDS()
        {
            LaborDtlListDataSet JobLaborListDS;
            LaborDtl JobLaborDtl;
            bool pgs;

            JobLaborDtl = new LaborDtl(this.Session.ConnectionPool);
            JobLaborListDS = new LaborDtlListDataSet();

            try
            {
                JobLaborListDS = JobLaborDtl.GetList("JobNum = \'" + this.Jobnumber + "\'", 0, 0, out pgs);

                return JobLaborListDS;
            }
            catch
            {
                return null;
            }
        }

        public PartTranListDataSet GetPartTranListDS()
        {
            bool pgs;
            PartTranListDataSet PartTranList = new PartTranListDataSet();
            PartTran MyPartTran = new PartTran(this.Session.ConnectionPool);

            try
            {
                PartTranList = MyPartTran.GetList("JobNum = \'" + this.Jobnumber + "\'", 0, 0, out pgs);
                return PartTranList;
            }
            catch
            {
                return null;
            }
        }

        public ChgLogDataSet GetChangeLogDS()
        {

            ChgLogDataSet ChgLogDS = new ChgLogDataSet();
            ChgLog MyChgLog = new ChgLog(this.Session.ConnectionPool);
            
            

            try
            {
                ChgLogDS = MyChgLog.GetChgLog("JobHead", this._jobDs.JobHead[0].RowIdent.ToString());
            }
            catch (Exception e)
            {
                MessageBox.Show(e.Message);
                return null;
            }
            return ChgLogDS;

        }


        public int GetLocation()
        {
            return Convert.ToInt32(this.GetField("Number01"));
        }

        public void ResetDS()
        {
            this.loadjob(this.Jobnumber);
        }

        public void SetLocation(int loc)
        {
            this._jobDs.AcceptChanges();
            this._jobDs.GetChanges();
            this._jobDs.JobHead.Rows[0]["Number01"] = loc;
            this._job.Update(this._jobDs);
        }

        public void IssueMtl(int AssembleySeq, int MtlSeq, string PartNum, decimal QtyPer)
        {
            string JobNum = this.Jobnumber;
            JobMtlSearchDataSet jobmtlDS = new JobMtlSearchDataSet();
            JobMtlSearch jobmtlsearch = new JobMtlSearch(Program.SConnPool.ConnectionPool);
            try
            {
                jobmtlDS = jobmtlsearch.GetByID(
                    JobNum,
                    AssembleySeq,
                    MtlSeq);
            }
            catch (Exception e)
            {
                MessageBox.Show("[Job.IssueMtl]" + e.Message + "\n" + 
                    e.InnerException.Message + "\n----\n" + JobNum.ToString() +
                    " / " + AssembleySeq.ToString() + " / " + MtlSeq.ToString());
                return;
            }
            IssueReturn ir = new IssueReturn(Program.SConnPool.ConnectionPool);
            IssueReturnDataSet irds = new IssueReturnDataSet();

            string pcmsg = "";

            ir.GetNewIssueReturnToJob(JobNum, AssembleySeq, "STK-MTL", "SwiftScan", out pcmsg, irds);

            irds.IssueReturn[0]["PartNum"] = PartNum;

            ir.OnChangePartNum(irds, "SwiftScan");

            irds.IssueReturn[0]["TranQty"] = QtyPer;


            Part partx = new Part(Program.SConnPool.ConnectionPool);
            PartDataSet partDS = new PartDataSet();

            bool reqinp;
            string msg = "";
            string allmsg = "";


            partDS = partx.GetByID(PartNum);

            irds.IssueReturn[0]["TranDate"] = DateTime.Now;
            irds.IssueReturn[0]["DimCode"] = partDS.Part.Rows[0]["IUM"].ToString();
            irds.IssueReturn[0]["FromWareHouseCode"] = "STORES"; //TODO: Ask Chris about this tooooo
            irds.IssueReturn[0]["FromBinNum"] = "001";
            irds.IssueReturn[0]["QtyRequired"] =
                Convert.ToDecimal(QtyPer);
            irds.IssueReturn[0]["ToJobSeq"] = MtlSeq;
            irds.IssueReturn[0]["ToWarehouseCode"] = "STORES";
            irds.IssueReturn[0]["ToBinNum"] = "001";
            irds.IssueReturn[0]["ToJobSeqPartNum"] = PartNum;
            irds.IssueReturn[0]["IssuedComplete"] = "true";
            irds.IssueReturn[0]["DimConvFactor"] = 1;
            irds.IssueReturn[0]["FromJobPlant"] = "MfgSys";
            irds.IssueReturn[0]["ToJobPlant"] = "MfgSys";
            irds.IssueReturn[0]["ProcessID"] = "SwiftScan";
            irds.IssueReturn[0]["OnHandUM"] = partDS.Part.Rows[0]["IUM"].ToString();
            irds.IssueReturn[0]["TranReference"] = "Assigned from SwiftScan";


            irds.IssueReturn[0]["UM"] = partDS.Part.Rows[0]["IUM"].ToString();
            irds.IssueReturn[0]["PartIUM"] = partDS.Part.Rows[0]["IUM"].ToString();
            irds.IssueReturn[0]["RequirementUOM"] = partDS.Part.Rows[0]["IUM"].ToString();
            irds.IssueReturn[0]["ToJobNum"] = JobNum;
            irds.IssueReturn[0]["ToJobPartNum"] = JobNum;

            ir.OnChangeTranQty(Convert.ToDecimal(QtyPer), irds);

            ir.PrePerformMaterialMovement(irds, out reqinp);
            if (reqinp == true)
                MessageBox.Show("Requires Input");
            string neg1, neg2;

            ir.NegativeInventoryTest(
                PartNum,
                "STORES",
                "001",
                "",
                "",
                0,
                QtyPer,
                out neg1,
                out neg2);
            try
            {
                ir.PerformMaterialMovement(true, irds, out msg, out allmsg);
            }
            catch (Exception em)
            {
                MessageBox.Show(em.Message + "\n" + em.InnerException.Message);
                throw;
            }
            
            allmsg += msg;


        }

    }


    class JobOperation
    {
        int assembly, operation;
        Job job;
        JobOperSearch JobOp;
        JobOperSearchDataSet JobOpData;
        public string errors { get; set; }
        bool Called_LaborOverride, Called_BurdenOverride, Called_PayrollOverride;

        DateTime payroll_override;
        decimal labor_override;
        decimal burden_override;

        public JobOperation(Job j, int oper, int assy = 0)
        {
            this.job = j;
            this.operation = oper;
            this.assembly = assy;

            try
            {
                JobOp = new JobOperSearch(job.Session.ConnectionPool);
                JobOpData = new JobOperSearchDataSet();
                JobOpData = JobOp.GetByID(job.Jobnumber, this.assembly, this.operation);
            }
            catch (Exception JobOpInit)
            {
                Log.LogThis(JobOpInit.Message, eloglevel.error);
                throw JobOpInit;
            }
        }

        public bool IsComplete()
        {
            if (this.JobOpData.JobOper[0]["OpComplete"].ToString() == "True")
                return true;
            else
                return false;
        }

        

        public void Complete(string EmpID, DateTime PayrollDate, int Qty, string Who, out string messages)
        {
            bool morepage;
            string msg;


            messages = "";

            if (this.Called_PayrollOverride == true)
                PayrollDate = this.payroll_override;

            Labor oLabor = new Labor(this.job.Session.ConnectionPool);
            LaborDataSet dsLabor = new LaborDataSet();
            decimal hrs = Convert.ToDecimal(this.JobOpData.JobOper[0]["EstProdHours"]);

            int clocktime = Convert.ToInt32(PayrollDate.Hour);
            if (PayrollDate.Minute != 0)
                clocktime += Convert.ToInt32(PayrollDate.Minute) / 60;

            try
            {

                dsLabor = oLabor.GetRowsCalendarView("EmployeeNum = \'" + EmpID + "\' AND PayrollDate = \'" + PayrollDate + "' BY PayrollDate", "", "", "", "", "", "", "", "", "", "", "", 0, 0, EmpID, PayrollDate, PayrollDate, out morepage);
                oLabor.GetNewLaborDtlNoHdr(dsLabor, EmpID, false, PayrollDate, clocktime, PayrollDate, clocktime);
                dsLabor.LaborHed.Rows[0]["FeedPayroll"] = false;
                
                oLabor.DefaultJobNum(dsLabor, this.job.Jobnumber);
                oLabor.DefaultOprSeq(dsLabor, this.operation, out msg); messages += msg;
                oLabor.DefaultLaborQty(dsLabor, Qty, out msg); messages += msg;
                oLabor.DefaultLaborHrs(dsLabor, hrs);
                oLabor.DefaultComplete(dsLabor, true, out msg); messages += msg;
                oLabor.CheckWarnings(dsLabor, out msg); messages += msg;
            }
            catch (BusinessObjectException e)
            {
                messages = e.Message;
            }
            catch (Exception e)
            {
                throw e;
            }

            decimal laborrate;

            if (this.Called_LaborOverride)
                laborrate = this.labor_override;
            else
                laborrate = Convert.ToDecimal(dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["LaborRate"]);

            if (this.Called_BurdenOverride)
                dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["BurdenRate"] = laborrate * burden_override;

            dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["TimeStatus"] = "A";
            dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["SubmittedBy"] = "SwiftScan";
            dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["ApprovedBy"] = "SwiftScan";
            dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["ApprovedDate"] = PayrollDate;
            dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["BurdenHrs"] = hrs;
            dsLabor.LaborDtl[dsLabor.LaborDtl.Count - 1]["LaborRate"] = laborrate;
            try
            {
                oLabor.Update(dsLabor);
                oLabor.SubmitForApproval(dsLabor, false, out msg); messages += msg;
            }
            catch (BusinessObjectException e)
            {
                messages += e.Message;
            }
            catch (Exception e)
            {
                throw e;
            }

        }

        /// <summary>
        /// Overrides the PayrollDate for the labor operation.
        /// </summary>
        /// <param name="pd">Date to apply labor to.</param>
        public void PayrollOverride(DateTime pd)
        {
            this.Called_PayrollOverride = true;
            this.payroll_override = pd;
        }

        /// <summary>
        /// Overrides the LaborRate.
        /// </summary>
        /// <param name="loval"></param>
        public void LaborOverride(decimal loval)
        {
            this.Called_LaborOverride = true;
            this.labor_override = loval;
        }

        /// <summary>
        /// Sets the burden rate to LaborRate * burval param.
        /// </summary>
        /// <param name="burval">Multiply LaborRate by this value and set it as the BurdenRate for the operation.</param>
        public void BurdenOverride(decimal burval)
        {
            this.Called_BurdenOverride = true;
            this.burden_override = burval;
        }

        /// <summary>
        /// Custom function to set JobHead.Number01 field to a numeric value corresponding with an oprseq.
        /// </summary>
        /// <returns>Returns error messages.</returns>
        public string Start_Operation()
        {
            JobStatus JobStat = new JobStatus(this.job.Session.ConnectionPool);
            JobStatusDataSet JobStatDS = new JobStatusDataSet();

            try
            {
                JobStatDS = JobStat.GetByID(this.job.Jobnumber);
                JobStatDS.JobHead.Rows[0]["Number01"] = this.operation.ToString();
                JobStat.Update(JobStatDS);
                return null;
            }
            catch (Exception e)
            {
                Log.LogThis(e.Message, eloglevel.error);
                return e.Message;
            }
        }



    }


    public class test
    {
        void ff()
        {
            Job myjob = new Job("011212");


            JobOperation jobop = new JobOperation(new Job("2222"), 220);
            jobop.Start_Operation();
            jobop = null;


            if (!jobop.IsComplete())
            {
                string errs;
                if (Properties.Settings.Default.LaborRateOverride == true)
                    jobop.LaborOverride(Properties.Settings.Default.LaborRateOverrideValue);
                if (Properties.Settings.Default.PayrollDateOverride == true)
                    jobop.PayrollOverride(Properties.Settings.Default.OverridePayrollDate);
                jobop.BurdenOverride(Properties.Settings.Default.BurdenRateMultiplier);

                jobop.Complete("1226", DateTime.Now, 1, "SwiftScan", out errs);
            }
            else
                return; //return "Operation already complete.";

        }
    }

}


