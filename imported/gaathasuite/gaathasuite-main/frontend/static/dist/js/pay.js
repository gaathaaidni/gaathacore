async function payInvoice(form){
  const data = new FormData(form);
  await fetch('/pay', {method:'POST', body: data});
  location.reload();
}
async function recordPayment(id){ location.href=`/pay/invoice/${id}/pay`; }
