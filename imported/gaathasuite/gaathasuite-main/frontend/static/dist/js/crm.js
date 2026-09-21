async function deleteCRM(id){
  if(!confirm('Delete?')) return;
  await apiDelete(`/crm/customers/${id}/delete`);
  location.reload();
}
async function deleteCustomer(id){
  if(!confirm('Delete customer?')) return;
  await apiDelete(`/crm/customer/${id}/delete`);
}
