using CrystalFinanceLibrary.Data;
using CrystalFinanceLibrary.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CrystalFinance.Api.Controllers;

[Route("api/[controller]")]
[ApiController]
[Authorize(Policy = "API.UserAccess")]
public class CrystalFinanceController(IMySqlDataService sqlCrud, ILogger<CrystalFinanceController> logger) : ControllerBase
{
    private readonly IMySqlDataService _data = sqlCrud;
    private readonly ILogger<CrystalFinanceController> _logger = logger;

    // GET: api/<CrystalFinanceController>
    [HttpGet]
    [ResponseCache(Duration = 300, VaryByQueryKeys = new[] { "pageNumber", "pageSize" })]
    public async Task<IActionResult> Get([FromQuery] int pageNumber = 1, [FromQuery] int pageSize = 20)
    {
        _logger.LogInformation("Retrieving transactions with paging. PageNumber: {PageNumber}, PageSize: {PageSize}", pageNumber, pageSize);

        try
        {
            var output = await _data.GetAllTransactionsAsync(pageNumber, pageSize);

            if (output.Items.Count == 0)
            {
                _logger.LogInformation("No transactions found for page {PageNumber}", pageNumber);
                return NotFound(new ApiResponse<object> { Success = false, Message = "No transactions found." });
            }

            _logger.LogInformation("Successfully retrieved {TransactionCount} transactions. PageNumber: {PageNumber}, TotalPages: {TotalPages}", 
                output.Items.Count, pageNumber, output.TotalPages);

            return Ok(new ApiResponse<PagedResult<TransactionModel>> { Success = true, Message = "Transactions retrieved successfully.", Data = output });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving transactions with paging. PageNumber: {PageNumber}, PageSize: {PageSize}", pageNumber, pageSize);
            return StatusCode(500, new ApiResponse<object>{Success=false, Message="An error occurred while retrieving transactions."});
        }
    }

    // GET api/<CrystalFinanceController>/5
    [HttpGet("{id:int:min(1)}")]
    [ResponseCache(Duration = 600, VaryByQueryKeys = new[] { "id" })]
    public async Task<IActionResult> Get(int id)
    {
        _logger.LogInformation("Retrieving transaction with ID: {TransactionId}", id);
        
        try
        {
            var output = await _data.GetTransactionById(id);
            
            if (output == null)
            {
                _logger.LogWarning("Transaction not found. ID: {TransactionId}", id);
                return NotFound(new ApiResponse<object> { Success = false, Message = $"Transaction with ID {id} not found." });
            }
            
            _logger.LogInformation("Successfully retrieved transaction. ID: {TransactionId}", id);
            return Ok(new ApiResponse<TransactionModel> { Success = true, Message = "Transaction retrieved successfully.", Data = output });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving transaction. ID: {TransactionId}", id);
            return StatusCode(500, new ApiResponse<object> { Success = false, Message = $"An error occurred while retrieving the transaction. ID: {id}" });
        }
    }

    // POST api/<CrystalFinanceController>
    [HttpPost]
    public async Task<IActionResult> Post([FromBody] TransactionModel value)
    {
        _logger.LogInformation("Adding new transaction. Amount: {Amount}, Description: {Description}", 
            value?.Amount, value?.Description);

        if (!ModelState.IsValid)
        {
            var errors = ModelState.Values.SelectMany(v => v.Errors).Select(e => e.ErrorMessage);
            _logger.LogWarning("Post request validation failed. Errors: {Errors}", string.Join(", ", errors));
            return BadRequest(new ApiResponse<object> { Success=false, Message = "Validation failed.", Data = errors });
        }

        if (value == null)
        {
            _logger.LogWarning("Post request received with null transaction data");
            return BadRequest( new ApiResponse<object>{ Success = false, Message = "Transaction data is required." });
        }

        try
        {
            await _data.AddTransaction(value);
            _logger.LogInformation("Transaction added successfully. Amount: {Amount}", value.Amount);
            return CreatedAtAction(nameof(Get), new { id = value.Id }, new ApiResponse<TransactionModel>
            {
                Success = true,
                Message = "Transaction created successfully.",
                Data = value
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding transaction. Amount: {Amount}", value.Amount);
            return StatusCode(500, new ApiResponse<object> { Success = false, Message = "An error occurred while adding the transaction." });
        }
    }

    // PUT api/<CrystalFinanceController>/5
    [HttpPut("{id:int:min(1)}")]
    public async Task<IActionResult> Put(int id, [FromBody] TransactionModel value)
    {
        _logger.LogInformation("Updating transaction. ID: {TransactionId}", id);

        if (!ModelState.IsValid)
        {
            var errors = ModelState.Values.SelectMany(v => v.Errors).Select(e => e.ErrorMessage);
            _logger.LogWarning("Put request validation failed. ID: {TransactionId}, Errors: {Errors}", id, string.Join(", ", errors));
            return BadRequest(new ApiResponse<object>{ Success = false, Message = "Validation failed.", Data = errors });
        }

        if (value == null)
        {
            _logger.LogWarning("Put request received with null transaction data. ID: {TransactionId}", id);
            return BadRequest(new ApiResponse<object> { Success = false, Message = "Transaction data is required." });
        }

        if (id != value.Id)
        {
            _logger.LogWarning("Transaction ID mismatch. URL ID: {UrlId}, Body ID: {BodyId}", id, value.Id);
            return BadRequest(new ApiResponse<object> { Success = false, Message = "Transaction ID mismatch." });
        }

        try
        {
            await _data.UpdateTransaction(value);
            _logger.LogInformation("Transaction updated successfully. ID: {TransactionId}", id);
            return Ok(new ApiResponse<TransactionModel>{ Success = true, Message = $"Transaction updated successfully. ID: {id}", Data = value});
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating transaction. ID: {TransactionId}", id);
            return StatusCode(500, new ApiResponse<object>{ Success = false, Message = $"An error occurred while updating the transaction. ID: {id}"});
        }
    }

    // DELETE api/<CrystalFinanceController>/5
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        _logger.LogInformation("Deleting transaction. ID: {TransactionId}", id);
        
        try
        {
            var existing = await _data.GetTransactionById(id);
            if (existing == null)
            {
                _logger.LogWarning("Delete request for non-existent transaction. ID: {TransactionId}", id);
                return NotFound(new ApiResponse<object> { Success=false,Message=$"Transaction not found. ID: {id}"});
            }

            await _data.DeleteTransaction(id);
            _logger.LogInformation("Transaction deleted successfully. ID: {TransactionId}", id);
            return Ok(new ApiResponse<object> { Success = true, Message = $"Transaction deleted successfully. ID: {id}", Data = id });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting transaction. ID: {TransactionId}", id);
            return StatusCode(500, new ApiResponse<object> { Success = false, Message = $"An error occurred while deleting the transaction. ID: {id}" });
        }
    }
}
