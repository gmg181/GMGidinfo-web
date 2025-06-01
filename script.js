function submitUID() {
  const uid = document.getElementById('uid-input').value;
  const result = document.getElementById('result');

  if (uid.length === 0) {
    result.innerHTML = "<p style='color: red;'>Please enter your UID.</p>";
  } else {
    result.innerHTML = `<p style='color: lightgreen;'>Welcome UID: ${uid}! Map loading...</p>`;
    // In real case, connect to backend or API here.
  }
}
