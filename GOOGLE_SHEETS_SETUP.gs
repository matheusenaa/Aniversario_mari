// ============================================================
// GOOGLE SHEETS - APPS SCRIPT (código para colar no Google)
// ============================================================
// Passo a passo:
// 1) Crie uma planilha no Google Sheets (ex.: "Aniversario Mari")
// 2) Menu: Extensões > Apps Script
// 3) Apague o conteúdo e cole este arquivo inteiro
// 4) Menu: Implantar > Nova implantação > Aplicativo da Web
//    - Descrição: "Recebe dados do site"
//    - Executar como: "Eu" (sua conta)
//    - Quem tem acesso: "Qualquer pessoa"
// 5) Clique em "Implantar" e copie a URL do Web App.
// 6) Configure a variável de ambiente GOOGLE_SHEETS_WEBAPP_URL no
//    Render (ou .env local) com essa URL.
//
// Colunas da planilha (linha 1 = cabeçalho):
//   A: Data/Hora
//   B: Nome
//   C: Presença
//   D: Presente
//   E: Acompanhantes
//   F: Mensagem

function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    var data = parsePayload(e);

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();

    // Cria o cabeçalho caso a planilha esteja vazia
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['Data/Hora', 'Nome', 'Presença', 'Presente', 'Acompanhantes', 'Mensagem']);
    }

    var dataHora = data.data_hora || new Date().toLocaleString('pt-BR');
    var nome = (data.nome || '').trim();
    var presenca = data.presenca || '';
    var presente = data.presente || '';
    var acompanhantes = data.acompanhantes || '';
    var mensagem = data.mensagem || '';

    // Tenta localizar uma linha existente com o mesmo nome (ignorando
    // maiúsculas/minúsculas e espaços extras) para evitar duplicidade.
    var rowIndex = findRowByNormalizedName(sheet, nome);

    if (rowIndex !== -1) {
      // Pessoa já existe: ATUALIZA a linha existente em vez de criar outra.
      var rowData = sheet.getRange(rowIndex, 1, 1, 6).getValues()[0];
      // Preserva outros valores não vazios e atualiza os campos recebidos.
      if (dataHora) rowData[0] = dataHora;
      if (presenca) rowData[2] = presenca;
      if (presente) rowData[3] = presente;
      if (acompanhantes) rowData[4] = acompanhantes;
      if (mensagem) rowData[5] = mensagem;
      sheet.getRange(rowIndex, 1, 1, 6).setValues([rowData]);
      return ContentService
        .createTextOutput(JSON.stringify({ status: 'ok', acao: 'atualizado', linha: rowIndex }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // Pessoa não existe: cria novo registro.
    sheet.appendRow([dataHora, nome, presenca, presente, acompanhantes, mensagem]);
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok', acao: 'criado' }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'erro', mensagem: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Busca uma linha onde a coluna B (Nome) corresponda ao nome informado,
// ignorando maiúsculas/minúsculas e espaços extras. Retorna o índice da linha
// (1-based) ou -1 se não encontrar.
function findRowByNormalizedName(sheet, nome) {
  if (!nome) return -1;
  var target = nome.toUpperCase();
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return -1; // só existe o cabeçalho

  var names = sheet.getRange(2, 2, lastRow - 1, 1).getValues();
  for (var i = 0; i < names.length; i++) {
    var lu = String(names[i][0] || '').trim().toUpperCase();
    // Comparação normalizada: remove múltiplos espaços internos
    var luNorm = lu.replace(/\s+/g, ' ');
    var targetNorm = target.replace(/\s+/g, ' ');
    if (luNorm === targetNorm) {
      return i + 2; // linha real na planilha
    }
  }
  return -1;
}

function parsePayload(e) {
  var data = {};

  // JSON (aplicação Flask envia JSON)
  if (e && e.postData && e.postData.contents && e.postData.type === 'application/json') {
    try {
      var parsed = JSON.parse(e.postData.contents);
      if (parsed && typeof parsed === 'object') {
        return parsed;
      }
    } catch (err) {
      // tenta o formato urlencoded abaixo
    }
  }

  // Formato application/x-www-form-urlencoded (fallback)
  if (e && e.parameter) {
    data.data_hora = e.parameter.data_hora || new Date().toLocaleString('pt-BR');
    data.nome = e.parameter.nome || '';
    data.presenca = e.parameter.presenca || '';
    data.presente = e.parameter.presente || '';
    data.acompanhantes = e.parameter.acompanhantes || '';
    data.mensagem = e.parameter.mensagem || '';
  }

  return data;
}