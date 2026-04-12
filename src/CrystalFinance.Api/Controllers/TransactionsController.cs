using CrystalFinanceLibrary.Logic;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace CrystalFinance.Api.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    [Authorize(Policy = "API.UserAccess")]
    public class TransactionsController(TransactionImportService importService, ILogger<TransactionsController> logger) : ControllerBase
    {
        private readonly TransactionImportService _importService = importService;
        private readonly ILogger<TransactionsController> _logger = logger;

        [HttpPost("import")]
        public async Task<IActionResult> ImportTransactions(IFormFile file, [FromQuery] string source)
        {
            _logger.LogInformation("Starting transaction import. Source: {Source}, FileName: {FileName}", source, file?.FileName);

            if (file == null || file.Length == 0)
            {
                _logger.LogWarning("Import request rejected. No file uploaded. Source: {Source}", source);
                return BadRequest("No file uploaded.");
            }

            if (string.IsNullOrWhiteSpace(source))
            {
                _logger.LogWarning("Import request rejected. No source specified. FileName: {FileName}", file.FileName);
                return BadRequest("Source parameter is required.");
            }

            try
            {
                _logger.LogInformation("Processing import file. FileName: {FileName}, FileSize: {FileSize} bytes, Source: {Source}", 
                    file.FileName, file.Length, source);

                using var stream = file.OpenReadStream();
                var records = await _importService.ImportTransactions(stream, source).ToListAsync();

                _logger.LogInformation("Transaction import completed successfully. RecordCount: {RecordCount}, Source: {Source}", 
                    records.Count, source);

                return Ok(new { message = $"Successfully imported {records.Count} transactions.", data = records });
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Invalid argument during import. Source: {Source}, FileName: {FileName}", source, file.FileName);
                return BadRequest($"Invalid input: {ex.Message}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error importing transactions. Source: {Source}, FileName: {FileName}", source, file.FileName);
                return StatusCode(500, "An error occurred while importing transactions.");
            }
        }
    }
}
