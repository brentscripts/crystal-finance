using CrystalFinanceLibrary.Data;
using CrystalFinanceLibrary.Logic;
using CrystalFinanceLibrary.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CrystalFinance.Api.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    [Authorize(Policy = "API.UserAccess")]
    public class TransactionsController(IMySqlDataService sqlCrud, TransactionImportService importService, ILogger<TransactionsController> logger) : ControllerBase
    {
        private readonly IMySqlDataService _data = sqlCrud;
        private readonly TransactionImportService _importService = importService;
        private readonly ILogger<TransactionsController> _logger = logger;

        [HttpPost("import")]
        public async Task<IActionResult> ImportTransactions(IFormFile file, [FromQuery] string source)
        {
            _logger.LogInformation("Starting transaction import. Source: {Source}, FileName: {FileName}", source, file?.FileName);

            if (file == null || file.Length == 0)
            {
                _logger.LogWarning("Import request rejected. No file uploaded. Source: {Source}", source);
                return BadRequest(new ApiResponse<object> { Success = false, Message = "No file uploaded." });
            }

            if (string.IsNullOrWhiteSpace(source))
            {
                _logger.LogWarning("Import request rejected. No source specified. FileName: {FileName}", file.FileName);
                return BadRequest(new ApiResponse<object> { Success = false, Message = "Source parameter is required." });
            }

            try
            {
                _logger.LogInformation("Processing import file. FileName: {FileName}, FileSize: {FileSize} bytes, Source: {Source}", 
                    file.FileName, file.Length, source);

                using var stream = file.OpenReadStream();
                var records = await _importService.ImportTransactions(stream, source).ToListAsync();

                _logger.LogInformation("Transaction import completed successfully. RecordCount: {RecordCount}, Source: {Source}", 
                    records.Count, source);

                if (records.Count == 0)
                {
                    return BadRequest(new ApiResponse<object>
                    {
                        Success = false,
                        Message = "The file was parsed but no valid transactions were found."
                    });
                }

                await _data.AddTransactionsRange(records);

                return Ok(new ApiResponse<List<TransactionModel>>{ Success = true, Message = $"Successfully imported {records.Count} transactions.", Data = records });
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Invalid argument during import. Source: {Source}, FileName: {FileName}", source, file.FileName);
                return BadRequest(new ApiResponse<object> { Success=false, Message = $"Invalid input: {ex.Message}" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error importing transactions. Source: {Source}, FileName: {FileName}", source, file.FileName);
                return StatusCode(500, new ApiResponse<object> { Success = false, Message ="An error occurred while importing transactions." });
            }
        }
    }
}
