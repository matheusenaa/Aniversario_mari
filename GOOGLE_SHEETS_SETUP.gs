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

    sheet.appendRow([
      data.data_hora || new Date().toLocaleString('pt-BR'),
      data.nome || '',
      data.presenca || '',
      data.presente || '',
      data.acompanhantes || '',
      data.mensagem || ''
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok' }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'erro', mensagem: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
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