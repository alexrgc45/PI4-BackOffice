import { apiRequest, clearSession } from "./api.js";

const form = document.querySelector("#work-create-form");
const clientSelect = document.querySelector("#work-client");
const workTypeSelect = document.querySelector("#work-type");
const materialInput = document.querySelector("#material-name");
const materialList = document.querySelector("#work-materials");
const upperTeeth = document.querySelector("#upper-teeth");
const lowerTeeth = document.querySelector("#lower-teeth");
const teethSelectionSummary = document.querySelector("#teeth-selection-summary");
const statusMessage = document.querySelector("#work-create-status");
const submitButton = document.querySelector("#create-work-button");
const createdWorkLink = document.querySelector("#created-work-link");
const filesList = document.querySelector("#work-files");
const imageFilesInput = document.querySelector("#image-files");
const otherFilesInput = document.querySelector("#other-files");
const teeth = [
    18, 17, 16, 15, 14, 13, 12, 11,
    21, 22, 23, 24, 25, 26, 27, 28,
    38, 37, 36, 35, 34, 33, 32, 31,
    41, 42, 43, 44, 45, 46, 47, 48,
];
const selectedMaterials = [];
const selectedTeeth = new Set();
const selectedFiles = [];
let optionsLoaded = false;

document.querySelector("#logout-button").addEventListener("click", () => {
    clearSession();
    window.location.replace("/");
});

function setStatus(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.classList.toggle("dashboard-status-error", isError);
}

function appendOptions(select, options, placeholder, labelForOption) {
    select.replaceChildren();
    const placeholderOption = document.createElement("option");
    placeholderOption.value = "";
    placeholderOption.textContent = placeholder;
    placeholderOption.disabled = true;
    placeholderOption.selected = true;
    select.append(placeholderOption);

    for (const optionData of options) {
        const option = document.createElement("option");
        option.value = String(optionData.id);
        option.textContent = labelForOption(optionData);
        select.append(option);
    }
}

function renderMaterials() {
    materialList.replaceChildren();
    for (const material of selectedMaterials) {
        const chip = document.createElement("span");
        chip.className = "work-create-material-chip";
        const name = document.createElement("span");
        name.textContent = material;
        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "×";
        removeButton.setAttribute("aria-label", `Remover ${material}`);
        removeButton.addEventListener("click", () => {
            selectedMaterials.splice(selectedMaterials.indexOf(material), 1);
            renderMaterials();
        });
        chip.append(name, removeButton);
        materialList.append(chip);
    }
}

function addMaterial() {
    const material = materialInput.value.trim();
    if (!material) {
        setStatus("Escreve o nome do material que pretendes adicionar.", true);
        materialInput.focus();
        return;
    }
    if (selectedMaterials.some((item) => item.toLocaleLowerCase("pt-PT")
        === material.toLocaleLowerCase("pt-PT"))) {
        setStatus("Esse material já foi adicionado.", true);
        materialInput.focus();
        return;
    }
    if (selectedMaterials.length >= 20) {
        setStatus("Podes adicionar no máximo 20 materiais.", true);
        return;
    }

    selectedMaterials.push(material);
    materialInput.value = "";
    renderMaterials();
    setStatus("Material adicionado.");
}

function renderTeeth() {
    upperTeeth.replaceChildren();
    lowerTeeth.replaceChildren();
    const upperNumbers = teeth.slice(0, 16);
    const lowerNumbers = teeth.slice(16);

    upperNumbers.forEach((toothNumber, index) => {
        upperTeeth.append(createToothButton(toothNumber, index, "upper"));
    });
    lowerNumbers.forEach((toothNumber, index) => {
        lowerTeeth.append(createToothButton(toothNumber, index, "lower"));
    });
    updateToothSelection();
}

function createToothButton(toothNumber, index, arch) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "odontogram-tooth";
    button.dataset.tooth = String(toothNumber);
    const distanceFromCenter = Math.abs(index - 7.5);
    const offset = arch === "upper"
        ? Math.round(distanceFromCenter * 2.2)
        : Math.round((7.5 - distanceFromCenter) * 2.2);
    button.style.setProperty("--arch-offset", `${offset}px`);
    button.setAttribute("aria-pressed", "false");
    button.setAttribute("aria-label", `Selecionar dente ${toothNumber}`);
    const shape = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    shape.setAttribute("viewBox", "0 0 48 54");
    shape.setAttribute("aria-hidden", "true");
    shape.classList.add("odontogram-tooth-shape");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute(
        "d",
        "M24 4C16 4 9 8 7 15c-2 7 2 12 4 19 2 8 2 15 7 15 3 0 4-8 6-12 2 4 3 12 6 12 5 0 5-7 7-15 2-7 6-12 4-19C39 8 32 4 24 4Z",
    );
    shape.append(path);
    const number = document.createElement("span");
    number.textContent = String(toothNumber);
    button.append(shape, number);
    button.addEventListener("click", () => {
        if (selectedTeeth.has(toothNumber)) {
            selectedTeeth.delete(toothNumber);
        } else {
            selectedTeeth.add(toothNumber);
        }
        updateToothSelection();
    });
    return button;
}

function updateToothSelection() {
    document.querySelectorAll(".odontogram-tooth").forEach((button) => {
        const toothNumber = Number(button.dataset.tooth);
        button.setAttribute(
            "aria-pressed",
            String(selectedTeeth.has(toothNumber)),
        );
    });
    const count = selectedTeeth.size;
    teethSelectionSummary.textContent = count === 0
        ? "Nenhum dente selecionado."
        : `${count} ${count === 1 ? "dente selecionado" : "dentes selecionados"}.`;
}

function renderFiles() {
    filesList.replaceChildren();
    selectedFiles.forEach(({ file }, index) => {
        const item = document.createElement("div");
        item.className = "work-create-file-item";
        const details = document.createElement("span");
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        details.textContent = `${file.name} · ${sizeMb} MB`;
        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.className = "permission-action";
        removeButton.textContent = "Remover";
        removeButton.setAttribute("aria-label", `Remover ficheiro ${file.name}`);
        removeButton.addEventListener("click", () => {
            selectedFiles.splice(index, 1);
            renderFiles();
        });
        item.append(details, removeButton);
        filesList.append(item);
    });
}

function addSelectedFiles(event) {
    const input = event.currentTarget;
    const files = Array.from(input.files);
    let validationMessage = "";
    let acceptedCount = 0;
    input.value = "";

    for (const file of files) {
        if (selectedFiles.length >= 5) {
            validationMessage = "Podes anexar no máximo 5 ficheiros.";
            break;
        }
        if (file.size === 0) {
            validationMessage ||= `O ficheiro "${file.name}" está vazio.`;
            continue;
        }
        if (file.size > 25 * 1024 * 1024) {
            validationMessage ||= `"${file.name}" excede o limite de 25 MB.`;
            continue;
        }
        const totalSize = selectedFiles.reduce((total, selected) => total + selected.file.size, 0);
        if (totalSize + file.size > 50 * 1024 * 1024) {
            validationMessage = "O tamanho total dos ficheiros não pode exceder 50 MB.";
            break;
        }

        selectedFiles.push({ file });
        acceptedCount += 1;
    }

    renderFiles();
    if (validationMessage) {
        setStatus(validationMessage, true);
    } else if (acceptedCount > 0) {
        setStatus(`${selectedFiles.length} ${selectedFiles.length === 1 ? "ficheiro selecionado" : "ficheiros selecionados"}.`);
    }
}

async function loadOptions() {
    try {
        const [user, clients, workTypes] = await Promise.all([
            apiRequest("/api/v1/auth/me/"),
            apiRequest("/api/v1/clientes/"),
            apiRequest("/api/v1/tipos-trabalho/"),
        ]);
        if (user.perfil !== "administrador") {
            clearSession();
            window.location.replace("/");
            return;
        }

        document.querySelector("#sidebar-email").textContent = user.email;
        const activeClients = clients.filter((client) => client.ativo);
        const activeWorkTypes = workTypes.filter((workType) => workType.ativo);
        appendOptions(
            clientSelect,
            activeClients,
            activeClients.length ? "Seleciona um cliente" : "Não existem clientes ativos",
            (client) => `${client.nome} · NIF ${client.nif}`,
        );
        appendOptions(
            workTypeSelect,
            activeWorkTypes,
            activeWorkTypes.length
                ? "Seleciona um tipo de trabalho"
                : "Não existem tipos de trabalho ativos",
            (workType) => workType.nome,
        );

        optionsLoaded = activeClients.length > 0 && activeWorkTypes.length > 0;
        submitButton.disabled = !optionsLoaded;
        if (optionsLoaded) {
            setStatus("Dados do formulário carregados.");
        } else {
            setStatus(
                "É necessário ter pelo menos um cliente e um tipo de trabalho ativos.",
                true,
            );
        }
    } catch (error) {
        setStatus(error.message || "Não foi possível carregar os dados do formulário.", true);
    }
}

document.querySelector("#add-material").addEventListener("click", addMaterial);
document.querySelector("#select-all-teeth").addEventListener("click", () => {
    teeth.forEach((toothNumber) => selectedTeeth.add(toothNumber));
    updateToothSelection();
});
document.querySelector("#clear-teeth").addEventListener("click", () => {
    selectedTeeth.clear();
    updateToothSelection();
});
imageFilesInput.addEventListener("change", addSelectedFiles);
otherFilesInput.addEventListener("change", addSelectedFiles);
materialInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        addMaterial();
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!optionsLoaded) {
        setStatus(
            "Não existem clientes ou tipos de trabalho disponíveis.",
            true,
        );
        return;
    }

    submitButton.disabled = true;
    setStatus("A criar trabalho…");
    const formData = new FormData(form);
    const uploadData = new FormData();
    uploadData.append("cliente", formData.get("cliente"));
    uploadData.append("paciente_nome", formData.get("paciente_nome").trim());
    uploadData.append("tipo_trabalho", formData.get("tipo_trabalho"));
    selectedMaterials.forEach((material) => uploadData.append("materiais", material));
    [...selectedTeeth]
        .sort((left, right) => left - right)
        .forEach((toothNumber) => uploadData.append("dentes", String(toothNumber)));
    if (formData.get("data_limite")) {
        uploadData.append("data_limite", formData.get("data_limite"));
    }
    uploadData.append("observacoes", formData.get("observacoes").trim());
    selectedFiles.forEach(({ file }) => uploadData.append("ficheiros", file, file.name));

    try {
        const work = await apiRequest("/api/v1/admin/trabalhos/", {
            method: "POST",
            body: uploadData,
        });
        const uploadedCount = work.ficheiros.length;
        const filesSummary = uploadedCount
            ? ` ${uploadedCount} ${uploadedCount === 1 ? "ficheiro anexado" : "ficheiros anexados"}.`
            : "";
        setStatus(`Trabalho #${work.id} criado com sucesso.${filesSummary}`);
        createdWorkLink.hidden = false;
        submitButton.textContent = "Trabalho criado";
        form.querySelectorAll("input, select, textarea, button").forEach((field) => {
            field.disabled = true;
        });
    } catch (error) {
        setStatus(error.message || "Não foi possível criar o trabalho.", true);
        submitButton.disabled = false;
    }
});

renderTeeth();
loadOptions();
