async function loadServices() {
  const container = document.querySelector("#services");
  try {
    const response = await fetch("/api/services");
    if (!response.ok) throw new Error("Service data unavailable");
    const services = await response.json();
    container.replaceChildren();
    if (services.length === 0) {
      container.innerHTML = '<p class="state">Noch keine Services veroeffentlicht.</p>';
      return;
    }
    const groups = new Map();
    services.forEach((service) => {
      const category = typeof service.category === "string" && service.category.trim()
        ? service.category.trim()
        : "Other";
      if (!groups.has(category)) groups.set(category, []);
      groups.get(category).push(service);
    });

    [...groups.entries()]
      .sort(([left], [right]) => left.localeCompare(right))
      .forEach(([category, categoryServices]) => {
        const group = document.createElement("section");
        group.className = "service-group";
        const heading = document.createElement("h2");
        heading.textContent = category;
        group.append(heading);
        const grid = document.createElement("div");
        grid.className = "service-grid";
        categoryServices
          .sort((left, right) => left.name.localeCompare(right.name))
          .forEach((service) => {
            const card = document.createElement("a");
            card.className = "service-card";
            card.href = service.url;
            const mark = document.createElement("span");
            mark.className = "service-mark";
            mark.textContent = service.icon || service.name.slice(0, 1);
            const details = document.createElement("span");
            const name = document.createElement("strong");
            name.textContent = service.name;
            const host = document.createElement("small");
            host.textContent = service.host;
            details.append(name, host);
            if (service.description) {
              const description = document.createElement("small");
              description.className = "description";
              description.textContent = service.description;
              details.append(description);
            }
            const runtime = document.createElement("small");
            runtime.className = "runtime";
            const statusText = service.status === "up"
              ? "Online"
              : service.status === "down" ? "Offline" : "Status unbekannt";
            const tlsText = service.tls ? "TLS" : "HTTP";
            const imageText = service.image && service.version
              ? ` · ${service.image}:${service.version}`
              : service.image ? ` · ${service.image}` : "";
            runtime.textContent = `${statusText} · ${tlsText}${imageText}`;
            details.append(runtime);
            const arrow = document.createElement("span");
            arrow.className = "arrow";
            arrow.textContent = "->";
            card.append(mark, details, arrow);
            grid.append(card);
          });
        group.append(grid);
        container.append(group);
      });
  } catch (error) {
    container.innerHTML = '<p class="state error">Services konnten nicht geladen werden.</p>';
  }
}

loadServices();
setInterval(loadServices, 30000);