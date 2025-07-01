document.addEventListener('DOMContentLoaded', function () {
    const pdfView = document.getElementById("pdf_renderer");
    const pdfContext = pdfView.getContext('2d');
    let pdfState = {
        pdf: null,
        currentPage: 1,
        zoom: 1,
    };
    let imagesPages = {};
    console.log("pdfView: ", pdfView);
    const renderPage = (pageNum) => {
        pdfState.pdf.getPage(pageNum).then(page => {
            const viewport = page.getViewport({ scale: pdfState.zoom });
            pdfView.width = viewport.width;
            pdfView.height = viewport.height;

            if (pdfView.width > screen.width) {
                adjustZoom();
            }

            page.render({ canvasContext: pdfContext, viewport }).promise.then(() => {
                adjustZoomImg();
            });
        });
    };

    const adjustZoom = () => {
        while (pdfView.width > screen.width) {
            pdfState.zoom -= 0.05;
            renderPage(pdfState.currentPage);
        }
    };

    const adjustZoomImg = () => {
        const firma = imagesPages[`page-${pdfState.currentPage}`];
        if (firma && firma.img) {
            firma.stage.setAttr('width', pdfView.width);
            firma.stage.setAttr('height', pdfView.height);
            firma.img.setAttr('x', firma.stage.width() * firma.percX);
            firma.img.setAttr('y', firma.stage.height() * firma.percY);
        }
    };

    document.getElementById('go_previous').addEventListener('click', () => {
        if (pdfState.currentPage <= 1) return;
        pdfState.currentPage--;
        renderPage(pdfState.currentPage);
    });

    document.getElementById('go_next').addEventListener('click', () => {
        if (pdfState.currentPage >= pdfState.pdf.numPages) return;
        pdfState.currentPage++;
        renderPage(pdfState.currentPage);
    });

    document.getElementById('zoom_in').addEventListener('click', () => {
        pdfState.zoom += 0.05;
        renderPage(pdfState.currentPage);
    });

    document.getElementById('zoom_out').addEventListener('click', () => {
        pdfState.zoom -= 0.05;
        renderPage(pdfState.currentPage);
    });

    document.getElementById('bntPegarFirma').addEventListener('click', () => {
        drawImage(imageFirmaPostition, pdfState.currentPage);
    });

    document.getElementById('bntQuitarFirma').addEventListener('click', () => {
        imagesPages[`page-${pdfState.currentPage}`] = null;
        document.getElementById(`page-${pdfState.currentPage}`).innerHTML = "";
    });

    document.getElementById('btnFirmar').addEventListener('click', () => {
        const firmas = [];
        Object.keys(imagesPages).forEach(key => {
            const pageNum = parseInt(key.split('-')[1]);
            const firma = imagesPages[key];
            if (firma && firma.img) {
                firmas.push({
                    x: firma.percX * pdfView.width,
                    y: pdfView.height - (firma.percY * pdfView.height) - firma.height,
                    width: firma.width,
                    height: firma.height,
                    numPage: pageNum
                });
            }
        });

        document.querySelector("textarea[name=txtFirmas]").value = JSON.stringify(firmas);
        document.getElementById('btnFirmarSubmit').click();
    });

    window.addEventListener('resize', () => renderPage(pdfState.currentPage));

    // Load PDF from the provided URL
    const loadPdf = (url) => {
        console.log(url);
        pdfjsLib.getDocument(url).promise.then(pdf => {
            pdfState.pdf = pdf;
            renderPage(pdfState.currentPage);
        });
    };

    // Replace with the actual URL or path to the PDF file
    loadPdf(document.querySelector("input[name=url_archivo]").value);
});
