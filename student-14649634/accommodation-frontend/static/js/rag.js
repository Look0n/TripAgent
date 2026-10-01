document.addEventListener(
    "DOMContentLoaded",
    function () {

        const ragEnabled =
            document.getElementById(
                "ragEnabled"
            );

        const ragModeStatus =
            document.getElementById(
                "ragModeStatus"
            );

        const ragServerStatusText =
            document.getElementById(
                "ragServerStatusText"
            );

        const ragServerStatusDot =
            document.getElementById(
                "ragServerStatusDot"
            );

        const ragQuestion =
            document.getElementById(
                "ragQuestion"
            );

        const ragK =
            document.getElementById(
                "ragK"
            );

        const ragResult =
            document.getElementById(
                "ragResult"
            ); 

        const ragButtons =
            document.querySelectorAll(
                ".rag-actions button"
            );

        let ragServerConnected = false;
            
            
        async function checkRAGServer() {

            try {
            
                const response = await fetch(
                    `${API_URL}/rag/health`
                );
            
                if (!response.ok) {
                    throw new Error(
                        "RAG server unavailable"
                    );
                }

                ragServerConnected = true;
            
                ragServerStatusText.textContent =
                    "Connected to shared RAG server";
            
                ragServerStatusDot.classList.remove(
                    "status-off",
                    "status-error"
                );
            
                ragServerStatusDot.classList.add(
                    "status-on"
                );
            
                ragQuestion.disabled = false;

                ragK.disabled = false;

                ragResult.textContent = 
                    "No RAG request yet.";
            
                ragButtons.forEach(
                    button => {
                        button.disabled = false;
                    }
                );
            
            } catch (error) {

                ragServerConnected = true;
        
                ragServerStatusText.textContent =
                    "Error - RAG server unavailable";
            
                ragServerStatusDot.classList.remove(
                    "status-on",
                    "status-off"
                );
            
                ragServerStatusDot.classList.add(
                    "status-error"
                );
            
                ragQuestion.disabled = true;
                ragK.disabled = true;
            
                ragButtons.forEach(
                    button => {
                        button.disabled = true;
                    }
                );
            
                ragResult.textContent =
                    "Unable to connect to the shared RAG server.";
            }
        }


        function updateRAGUI() {

            if (ragEnabled.checked) {

                ragModeStatus.textContent =
                    "ON";
                
                checkRAGServer();

            } else {

                ragModeStatus.textContent =
                    "OFF";

                ragQuestion.disabled = true;

                ragK.disabled = true;

                ragServerStatusText.textContent =
                    "Disconnected";

                ragServerStatusDot.classList.remove(
                    "status-on",
                    "status-error"
                );

                ragServerStatusDot.classList.add(
                    "status-off"
                );

                ragResult.textContent = 
                    "RAG service is disabled.";
            }
        }


        ragEnabled.addEventListener(
            "change",
            updateRAGUI
        );

        updateRAGUI();


        window.answerWithRAG =
            async function () {

                if (
                    !ragEnabled.checked ||
                    !ragServerConnected
                ) {
                    return;
                }

                const question =
                    ragQuestion.value.trim();

                if (!question) {

                    ragResult.textContent =
                        "Please enter a question.";

                    return;
                }

                ragResult.textContent =
                    "Generating grounded answer...";


                try {

                    const response =
                        await fetch(
                            `${API_URL}/rag`,
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify({
                                        question:
                                            question,
                                        k:
                                            Number(
                                                ragK.value
                                            )
                                    })
                            }
                        );


                    const data =
                        await response.json();


                    ragResult.textContent =
                        JSON.stringify(
                            data,
                            null,
                            2
                        );


                } catch (error) {

                    console.error(error);

                    ragResult.textContent =
                        "Unable to connect to RAG service.";
                }
            };


        window.retrieveRAGContext =
            async function () {
        
                if (
                    !ragEnabled.checked ||
                    !ragServerConnected
                ) {
                    return;
                }
        
                const question =
                    ragQuestion.value.trim();
        
                if (!question) {
        
                    ragResult.textContent =
                        "Please enter a question.";
        
                    return;
                }
        
                ragResult.textContent =
                    "Retrieving context...";
        
                try {
        
                    const response = await fetch(
                        `${API_URL}/rag/retrieve`,
                        {
                            method: "POST",
        
                            headers: {
                                "Content-Type":
                                    "application/json"
                            },
        
                            body: JSON.stringify({
                                question: question,
                                k: Number(
                                    ragK.value
                                )
                            })
                        }
                    );
        
                    const data =
                        await response.json();
        
                    ragResult.textContent =
                        JSON.stringify(
                            data,
                            null,
                            2
                        );
        
                } catch (error) {
        
                    console.error(error);
        
                    ragResult.textContent =
                        "Unable to retrieve RAG context.";
                }
            };


        window.refreshRAGCorpus =
            async function () {
        
                if (
                    !ragEnabled.checked ||
                    !ragServerConnected
                ) {
                    return;
                }
        
                ragResult.textContent =
                    "Refreshing Accommodation corpus...";
        
                try {
        
                    const response = await fetch(
                        `${API_URL}/rag/refresh`,
                        {
                            method: "POST",
        
                            headers: {
                                "Content-Type":
                                    "application/json"
                            }
                        }
                    );
        
                    const data =
                        await response.json();
        
                    ragResult.textContent =
                        JSON.stringify(
                            data,
                            null,
                            2
                        );
        
                } catch (error) {
        
                    console.error(error);
        
                    ragResult.textContent =
                        "Unable to refresh RAG corpus.";
                }
            };
            
    }
);
