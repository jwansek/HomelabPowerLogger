$(document).ready(function() {
    fetch("/api/mikrotik_plug").then((resp) => {
        resp.json().then((body) => {
            const MIKROTIK_PARENT = body["parent"];

            const parent_elem = document.getElementById("tr_" + MIKROTIK_PARENT);

            fetch("/api/mikrotik_devices").then((resp) => {
                resp.json().then((body) => {
                    Object.keys(body).reverse().forEach((interface, i) => {
                        let tr_elem = document.createElement("tr");
                        tr_elem.classList.add("mikrotik_tr")
                        tr_elem.id = "mikrotik_tr_" + interface;
                        // console.log(interface, body[interface]);
                        parent_elem.parentNode.insertBefore(tr_elem, parent_elem.nextSibling);

                        for (let i = 0; i <= 4; i++) {
                            let td_elem = document.createElement("td");
                            if (i === 0) {
                                td_elem.innerHTML = interface;
                                td_elem.classList.add("mikrotik_interface_name")
                            } else if (i === 1) {
                                td_elem.innerHTML = body[interface];
                            } else if (i === 2) {
                                td_elem.id = "mikrotik_td_" + interface + "_watts_now";
                            } else if (i === 3) {
                                td_elem.id = "mikrotik_td_" + interface + "_watts_yesterday";
                            }
                            tr_elem.appendChild(td_elem);
                        }
                    });

                    get_mikrotik_table(Object.keys(body));
                });
            });
        });
    });

    get_main_table();
})

function get_mikrotik_table(interfaces) {
    interfaces.forEach((interface) => {
        fetch("/api/mikrotik_interface/" + interface).then((resp) => {
            resp.json().then((body) => {
                console.log(body["poe_status"]);
                // TODO: Add a delay if it was cached
            });
        });
    });

    setTimeout(function() {get_mikrotik_table(interfaces);}, 1000)
}

function get_main_table() {
    fetch("/api/plugs").then((resp) => {
        resp.json().then((body) => {
            let watts_sum = 0;
            let kwh_sum = 0;
            Object.keys(body).forEach((host, i) => {
                watts = body[host]["watts"];
                kwh = body[host]["kWh"];
                document.getElementById(host + "_watts_now").innerHTML = watts[1];
                document.getElementById(host + "_watts_yesterday").innerHTML = kwh[1];
                watts_sum += watts[1];
                kwh_sum += kwh[1];
                
                document.getElementById("watts_last_updated").innerHTML = "Current power usage last updated at " + watts[0];
                document.getElementById("kwh_last_updated").innerHTML = "Yesterday's power usage last updated at " + kwh[0];

                console.log(host, watts[0], watts[1], kwh[1])
            });
            document.getElementById("sum_watts_now").innerHTML = watts_sum;
            document.getElementById("sum_watts_yesterday").innerHTML = kwh_sum;
        });
    });

    setTimeout(get_main_table, 10000);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}