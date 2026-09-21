async function deleteEmployee(id){ if(!confirm('Delete employee?')) return; await apiDelete(`/hr/employee/${id}/delete`); }
