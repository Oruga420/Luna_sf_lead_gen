document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('leadGenForm');
    const resultDiv = document.getElementById('result');
    const downloadCsvButton = document.getElementById('downloadCsv');
    const progressBar = document.createElement('progress');
    progressBar.max = 100;
    progressBar.value = 0;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        resultDiv.innerHTML = 'Generating leads...';
        resultDiv.appendChild(progressBar);
        downloadCsvButton.style.display = 'none';

        const webToLeadHtml = document.getElementById('webToLeadHtml').value;
        const numLeads = document.getElementById('numLeads').value;
        const inspiration = document.getElementById('inspiration').value;
        const useCase = document.getElementById('useCase').value;

        try {
            const response = await fetch('/generate_leads', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ webToLeadHtml, numLeads, inspiration, useCase }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value);
                const events = text.split('\n\n');

                for (const event of events) {
                    if (event.startsWith('data:')) {
                        const data = JSON.parse(event.slice(5));
                        progressBar.value = data.progress;
                        resultDiv.innerHTML = `<p>${data.message}</p>`;
                        resultDiv.appendChild(progressBar);

                        if (data.progress === 100) {
                            if (data.results && data.results.length > 0) {
                                resultDiv.innerHTML += '<h4>Submission Results:</h4><ul>';
                                data.results.forEach((result, index) => {
                                    resultDiv.innerHTML += `<li>Lead ${index + 1}: ${result.success ? 'Submitted successfully' : 'Failed to submit'}</li>`;
                                });
                                resultDiv.innerHTML += '</ul>';
                            }
                            downloadCsvButton.style.display = 'block';
                        }
                    }
                }
            }
        } catch (error) {
            resultDiv.innerHTML = `<h3>Error</h3><p>An unexpected error occurred. Please try again.</p>`;
            console.error('Error generating leads:', error);
        }
    });

    downloadCsvButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/download_csv');
            if (response.ok) {
                const contentDisposition = response.headers.get('Content-Disposition');
                const filenameMatch = contentDisposition && contentDisposition.match(/filename="?(.+)"?/i);
                const filename = filenameMatch ? filenameMatch[1] : 'generated_leads.csv';

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const errorData = await response.json();
                console.error('Error downloading CSV:', errorData.error);
                alert(`Error downloading CSV: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error downloading CSV:', error);
            alert('An error occurred while downloading the CSV file.');
        }
    });
});
