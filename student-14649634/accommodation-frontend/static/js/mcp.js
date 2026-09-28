document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log("mcp.js loaded");


        const mcpEnabled =
            document.getElementById(
                "mcpEnabled"
            );

        const mcpModeStatus =
            document.getElementById(
                "mcpModeStatus"
            );

        const mcpTool =
            document.getElementById(
                "mcpTool"
            );

        const mcpArguments =
            document.getElementById(
                "mcpArguments"
            );

        const mcpResult =
            document.getElementById(
                "mcpResult"
            );

        const mcpServerStatusText =
            document.getElementById(
                "mcpServerStatusText"
            );

        const mcpServerStatusDot =
            document.getElementById(
                "mcpServerStatusDot"
            );

        const mcpToolGrid = 
            document.getElementById(
                "mcpToolGrid"
            );

        const mcpToolText = 
            document.getElementById(
                "mcpToolText"
            );


        console.log({
            mcpEnabled,
            mcpModeStatus,
            mcpTool,
            mcpArguments,
            mcpResult
        });

        const mcpExamples = {

            get_accommodations: {},

            get_accommodation_by_city: {
                city: "Sydney"
            },

            search_accommodations: {
                city: "Sydney",
                max_price: 400,
                guests: 2,
                type: "Hotel"
            },

            check_accommodation_availability: {
                accommodation_id: 2,
                check_in: "2026-10-05",
                check_out: "2026-10-08"
            },

            list_tripagent_services: {},

            get_service_status: {
                service_name:
                    "accommodation"
            },

            list_available_tools: {
                feature:
                    "accommodation"
            },

            get_tripagent_help: {
                topic: "mcp"
            },

            get_system_summary: {}
        };

        let mcpServerConnected = false;

        async function checkMCPServer() {

            try {
        
                const response = await fetch(
                    `${API_URL}/mcp/health`
                );
        
                if (!response.ok) {
                    throw new Error(
                        "MCP server unavailable"
                    );
                }
        
                mcpServerConnected = true;
        
                mcpServerStatusText.textContent =
                    "Connected to shared MCP server";
        
                mcpServerStatusDot.classList.remove(
                    "status-off",
                    "status-error"
                );
        
                mcpServerStatusDot.classList.add(
                    "status-on"
                );
        
                mcpTool.disabled = false;
                mcpArguments.disabled = false;
        
                mcpToolGrid.style.display =
                    "block";
        
                mcpToolText.textContent =
                    "MCP Mode is available with tools below:";
        
                mcpResult.textContent =
                    "No tool called yet.";
        
            } catch (error) {
        
                mcpServerConnected = false;
        
                mcpServerStatusText.textContent =
                    "Error - MCP server unavailable";
        
                mcpServerStatusDot.classList.remove(
                    "status-on",
                    "status-off"
                );
        
                mcpServerStatusDot.classList.add(
                    "status-error"
                );
        
                mcpTool.disabled = true;
                mcpArguments.disabled = true;
        
                mcpToolGrid.style.display =
                    "none";
        
                mcpToolText.textContent =
                    "Unable to connect to MCP server.";
        
                mcpResult.textContent =
                    "Unable to connect to the shared MCP server.";
            }
        }


        function updateMCPUI() {

            if (mcpEnabled.checked) {
        
                mcpModeStatus.textContent =
                    "ON";
        
                checkMCPServer();
        
            } else {
        
                mcpServerConnected = false;
        
                mcpModeStatus.textContent =
                    "OFF";
        
                mcpTool.disabled = true;
                mcpArguments.disabled = true;
        
                mcpServerStatusText.textContent =
                    "Disconnected";
        
                mcpServerStatusDot.classList.remove(
                    "status-on",
                    "status-error"
                );
        
                mcpServerStatusDot.classList.add(
                    "status-off"
                );
        
                mcpToolGrid.style.display =
                    "none";
        
                mcpToolText.textContent =
                    "MCP Mode is disabled.";
        
                mcpResult.textContent =
                    "MCP Mode is disabled.";
            }
        }


        mcpEnabled.addEventListener(
            "change",
            updateMCPUI
        );
        
        updateMCPUI();


        function updateMCPArguments() {

            const example =
                mcpExamples[
                    mcpTool.value
                ] || {};
        
            mcpArguments.value =
                JSON.stringify(
                    example,
                    null,
                    2
                );
        }
        
        
        mcpTool.addEventListener(
            "change",
            updateMCPArguments
        );

        updateMCPArguments();


        window.callMCPTool =
            async function () {

                if (
                    !mcpEnabled.checked ||
                    !mcpServerConnected
                ) {
                    mcpResult.textContent =
                        "MCP Mode is not connected.";

                    return;
                }


                const tool =
                    mcpTool.value;

                const argumentsText =
                    mcpArguments
                        .value
                        .trim();


                if (!tool) {

                    mcpResult.textContent =
                        "Please select a tool.";

                    return;
                }


                let argumentsData = {};

                try {

                    argumentsData =
                        argumentsText
                            ? JSON.parse(
                                argumentsText
                            )
                            : {};

                } catch (error) {

                    mcpResult.textContent =
                        "Arguments must be valid JSON.";

                    return;
                }


                mcpResult.textContent =
                    `Calling ${tool}...`;


                try {

                    const response =
                        await fetch(
                            `${API_URL}/mcp/call`,
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json",
                                    "X-MCP-Mode":
                                        mcpEnabled.checked ? "on" : "off"
                                },

                                body:
                                    JSON.stringify({
                                        tool:
                                            tool,
                                        arguments:
                                            argumentsData
                                    })
                            }
                        );


                    const data =
                        await response.json();


                    mcpResult.textContent =
                        JSON.stringify(
                            data,
                            null,
                            2
                        );


                } catch (error) {

                    console.error(
                        error
                    );

                    mcpResult.textContent =
                        "Unable to connect to MCP service.";
                }
            };
    }
);