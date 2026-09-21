async function createPayslip(empId, form){
  const data = new FormData(form);
  await fetch(`/employees/${empId}/payslip`, {method:'POST', body: data});
  location.reload();
}
async function deleteEmployee(id){ if(!confirm('Delete employee?')) return; await apiDelete(`/payroll/employee/${id}/delete`); }
