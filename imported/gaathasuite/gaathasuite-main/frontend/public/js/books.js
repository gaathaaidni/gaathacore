async function deleteInvoice(id){
  if(!confirm('Delete invoice?')) return;
  await apiDelete(`/books/invoice/${id}/delete`);
}
