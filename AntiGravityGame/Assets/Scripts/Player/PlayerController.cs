using UnityEngine;
using AntiGravity.Core;
using AntiGravity.Data;
using AntiGravity.Gravity;

namespace AntiGravity.Player
{
    /// <summary>
    /// Third-person player controller with gravity-aware movement.
    /// 
    /// Features:
    /// - Gravity-relative movement (moves along current gravity's "ground" plane)
    /// - Smooth orientation to match gravity direction (walk on ceilings/walls)
    /// - Variable jump height based on current gravity strength
    /// - Ground detection via spherecast
    /// - Air control with configurable responsiveness
    /// - Mobile touch input support via Unity's Input System
    /// - Coyote time and jump buffering for responsive platforming
    /// 
    /// Requires: Rigidbody, CapsuleCollider, GravityAffectedObject
    /// </summary>
    [RequireComponent(typeof(Rigidbody))]
    [RequireComponent(typeof(CapsuleCollider))]
    [RequireComponent(typeof(GravityAffectedObject))]
    public class PlayerController : MonoBehaviour
    {
        [Header("=== Movement ===")]
        [Tooltip("Maximum ground movement speed (m/s)")]
        [SerializeField] private float moveSpeed = 8f;

        [Tooltip("Acceleration when on ground")]
        [SerializeField] private float groundAcceleration = 50f;

        [Tooltip("Deceleration when input is released (ground)")]
        [SerializeField] private float groundDeceleration = 40f;

        [Tooltip("Air movement multiplier (0 = no air control, 1 = full)")]
        [Range(0f, 1f)]
        [SerializeField] private float airControlFactor = 0.4f;

        [Tooltip("Speed multiplier in low/zero gravity environments")]
        [SerializeField] private float lowGravitySpeedMultiplier = 1.3f;

        [Tooltip("Rotation speed for turning (degrees/sec)")]
        [SerializeField] private float rotationSpeed = 720f;

        [Header("=== Jumping ===")]
        [Tooltip("Base jump force (adjusted by gravity strength)")]
        [SerializeField] private float jumpForce = 12f;

        [Tooltip("Jump force multiplier in low gravity (makes jumps higher)")]
        [SerializeField] private float lowGravityJumpMultiplier = 1.8f;

        [Tooltip("Maximum jumps (1 = single, 2 = double jump)")]
        [Range(1, 3)]
        [SerializeField] private int maxJumps = 2;

        [Tooltip("Coyote time: seconds after leaving ground where jump still counts")]
        [Range(0f, 0.5f)]
        [SerializeField] private float coyoteTime = 0.15f;

        [Tooltip("Jump buffer: seconds before landing where jump input is remembered")]
        [Range(0f, 0.5f)]
        [SerializeField] private float jumpBufferTime = 0.1f;

        [Header("=== Ground Detection ===")]
        [Tooltip("Layers considered as ground")]
        [SerializeField] private LayerMask groundLayers = ~0;

        [Tooltip("Distance below feet to check for ground")]
        [SerializeField] private float groundCheckDistance = 0.15f;

        [Tooltip("Radius of ground check sphere")]
        [SerializeField] private float groundCheckRadius = 0.3f;

        [Header("=== Gravity Orientation ===")]
        [Tooltip("Speed at which player rotates to match gravity direction (degrees/sec)")]
        [SerializeField] private float gravityAlignmentSpeed = 180f;

        [Tooltip("Minimum gravity change to trigger re-orientation")]
        [SerializeField] private float gravityChangeThreshold = 0.5f;

        [Header("=== Camera Reference ===")]
        [Tooltip("Reference to the third-person camera for movement direction")]
        [SerializeField] private Transform cameraTransform;

        [Header("=== Mobile Input ===")]
        [Tooltip("Virtual joystick dead zone")]
        [Range(0f, 0.3f)]
        [SerializeField] private float joystickDeadZone = 0.1f;

        // ─── Public State ───
        public bool IsGrounded { get; private set; }
        public bool IsMoving { get; private set; }
        public Vector3 Velocity => _rigidbody.linearVelocity;
        public float CurrentSpeed => _horizontalVelocity.magnitude;
        public int JumpsRemaining { get; private set; }
        public Vector3 CurrentGravityUp => _gravityUp;

        // ─── Internal ───
        private Rigidbody _rigidbody;
        private CapsuleCollider _capsule;
        private GravityAffectedObject _gravityObject;

        // Gravity orientation
        private Vector3 _gravityUp = Vector3.up;        // "Up" relative to current gravity
        private Quaternion _targetOrientation;
        private Vector3 _lastGravityDirection;

        // Movement
        private Vector3 _moveInput;
        private Vector3 _horizontalVelocity;
        private Vector3 _worldMoveDirection;

        // Jumping
        private int _jumpCount;
        private float _coyoteTimer;
        private float _jumpBufferTimer;
        private bool _jumpRequested;

        // Ground check
        private RaycastHit _groundHit;

        // ─── Lifecycle ───

        private void Awake()
        {
            _rigidbody = GetComponent<Rigidbody>();
            _capsule = GetComponent<CapsuleCollider>();
            _gravityObject = GetComponent<GravityAffectedObject>();

            // Configure rigidbody for character control
            _rigidbody.freezeRotation = true; // We handle rotation manually
            _rigidbody.interpolation = RigidbodyInterpolation.Interpolate;
            _rigidbody.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;

            _lastGravityDirection = Vector3.down;
            _targetOrientation = transform.rotation;
            JumpsRemaining = maxJumps;

            // Auto-find camera if not assigned
            if (cameraTransform == null && Camera.main != null)
                cameraTransform = Camera.main.transform;
        }

        private void Update()
        {
            // Gather input (Update for responsiveness, apply in FixedUpdate)
            GatherInput();

            // Tick timers
            UpdateTimers();
        }

        private void FixedUpdate()
        {
            // 1. Update gravity orientation
            UpdateGravityOrientation();

            // 2. Ground detection
            CheckGrounded();

            // 3. Apply movement
            ApplyMovement();

            // 4. Handle jumping
            HandleJump();

            // 5. Update player rotation to face movement direction
            UpdateFacingRotation();
        }

        // ─── Input Gathering ───

        private void GatherInput()
        {
            // Read movement input (works with keyboard, gamepad, and virtual joystick)
            float horizontal = Input.GetAxisRaw("Horizontal");
            float vertical = Input.GetAxisRaw("Vertical");

            _moveInput = new Vector3(horizontal, 0f, vertical);

            // Apply dead zone for mobile joystick
            if (_moveInput.magnitude < joystickDeadZone)
                _moveInput = Vector3.zero;
            else
                _moveInput = _moveInput.normalized *
                    Mathf.InverseLerp(joystickDeadZone, 1f, _moveInput.magnitude);

            // Clamp to unit circle
            if (_moveInput.magnitude > 1f)
                _moveInput.Normalize();

            IsMoving = _moveInput.sqrMagnitude > 0.01f;

            // Jump input (buffered)
            if (Input.GetButtonDown("Jump"))
            {
                _jumpRequested = true;
                _jumpBufferTimer = jumpBufferTime;
            }
        }

        private void UpdateTimers()
        {
            // Coyote time countdown
            if (!IsGrounded)
                _coyoteTimer -= Time.deltaTime;

            // Jump buffer countdown
            if (_jumpBufferTimer > 0f)
                _jumpBufferTimer -= Time.deltaTime;
            else
                _jumpRequested = false;
        }

        // ─── Gravity Orientation ───

        /// <summary>
        /// Updates the player's "up" direction to match the current gravity.
        /// Allows walking on walls/ceilings when gravity direction changes.
        /// </summary>
        private void UpdateGravityOrientation()
        {
            Vector3 currentGravity = _gravityObject.CurrentGravity;

            // Determine "up" as opposite of gravity direction
            if (currentGravity.sqrMagnitude > 0.01f)
            {
                Vector3 newGravityDir = currentGravity.normalized;

                // Only re-orient if gravity direction changed significantly
                if (Vector3.Angle(-newGravityDir, _gravityUp) > gravityChangeThreshold)
                {
                    _gravityUp = -newGravityDir;
                    _lastGravityDirection = newGravityDir;
                }
            }
            else
            {
                // Zero gravity — maintain current orientation
                _gravityUp = transform.up;
            }

            // Smoothly rotate to align with gravity
            Quaternion targetRot = Quaternion.FromToRotation(transform.up, _gravityUp)
                * transform.rotation;

            transform.rotation = Quaternion.RotateTowards(
                transform.rotation,
                targetRot,
                gravityAlignmentSpeed * Time.fixedDeltaTime);
        }

        // ─── Ground Detection ───

        private void CheckGrounded()
        {
            bool wasGrounded = IsGrounded;

            // Spherecast downward (relative to current gravity "down")
            Vector3 castOrigin = transform.position + _gravityUp * (_capsule.radius * 0.9f);
            Vector3 castDir = -_gravityUp;

            IsGrounded = Physics.SphereCast(
                castOrigin,
                groundCheckRadius,
                castDir,
                out _groundHit,
                _capsule.radius + groundCheckDistance,
                groundLayers,
                QueryTriggerInteraction.Ignore);

            // Landing detection
            if (!wasGrounded && IsGrounded)
            {
                OnLanded();
            }

            // Leaving ground detection (start coyote time)
            if (wasGrounded && !IsGrounded)
            {
                _coyoteTimer = coyoteTime;
            }
        }

        // ─── Movement ───

        private void ApplyMovement()
        {
            if (!IsMoving && IsGrounded)
            {
                // Decelerate on ground when no input
                _horizontalVelocity = Vector3.MoveTowards(
                    _horizontalVelocity,
                    Vector3.zero,
                    groundDeceleration * Time.fixedDeltaTime);
            }
            else if (IsMoving)
            {
                // Calculate camera-relative movement direction
                _worldMoveDirection = CalculateCameraRelativeDirection(_moveInput);

                // Determine target speed
                float targetSpeed = moveSpeed;
                float gravityMult = GravityManager.Instance?.GetGravityMultiplierAtPoint(
                    transform.position) ?? 1f;

                if (gravityMult < 0.7f)
                    targetSpeed *= lowGravitySpeedMultiplier;

                Vector3 targetVelocity = _worldMoveDirection * targetSpeed;

                // Accelerate toward target
                float accel = IsGrounded ? groundAcceleration :
                    groundAcceleration * airControlFactor;

                _horizontalVelocity = Vector3.MoveTowards(
                    _horizontalVelocity,
                    targetVelocity,
                    accel * Time.fixedDeltaTime);
            }

            // Decompose current velocity into gravity-aligned components
            Vector3 verticalVel = Vector3.Project(_rigidbody.linearVelocity, _gravityUp);
            _rigidbody.linearVelocity = verticalVel + _horizontalVelocity;
        }

        /// <summary>
        /// Converts local input (WASD) into world-space direction relative to camera.
        /// Projects onto the player's current gravity plane.
        /// </summary>
        private Vector3 CalculateCameraRelativeDirection(Vector3 input)
        {
            if (cameraTransform == null) return input;

            // Get camera forward/right projected onto gravity plane
            Vector3 camForward = Vector3.ProjectOnPlane(cameraTransform.forward, _gravityUp);
            Vector3 camRight = Vector3.ProjectOnPlane(cameraTransform.right, _gravityUp);

            if (camForward.sqrMagnitude < 0.001f)
                camForward = Vector3.ProjectOnPlane(cameraTransform.up, _gravityUp);

            camForward.Normalize();
            camRight.Normalize();

            return (camForward * input.z + camRight * input.x).normalized;
        }

        // ─── Jumping ───

        private void HandleJump()
        {
            bool canJump = (IsGrounded || _coyoteTimer > 0f || JumpsRemaining > 0)
                && JumpsRemaining > 0;

            if (_jumpRequested && canJump)
            {
                PerformJump();
                _jumpRequested = false;
                _jumpBufferTimer = 0f;
            }
        }

        private void PerformJump()
        {
            // Cancel downward velocity
            Vector3 vel = _rigidbody.linearVelocity;
            float verticalSpeed = Vector3.Dot(vel, _gravityUp);
            if (verticalSpeed < 0f)
            {
                vel -= _gravityUp * verticalSpeed;
                _rigidbody.linearVelocity = vel;
            }

            // Calculate jump force based on current gravity
            float currentJumpForce = jumpForce;
            float gravityMult = GravityManager.Instance?.GetGravityMultiplierAtPoint(
                transform.position) ?? 1f;

            if (gravityMult < 0.7f)
                currentJumpForce *= lowGravityJumpMultiplier;

            // Apply jump impulse upward (relative to current gravity)
            _rigidbody.AddForce(_gravityUp * currentJumpForce, ForceMode.Impulse);

            JumpsRemaining--;
            _coyoteTimer = 0f; // Consume coyote time
            IsGrounded = false;
        }

        private void OnLanded()
        {
            JumpsRemaining = maxJumps;

            // Check for buffered jump
            if (_jumpBufferTimer > 0f && _jumpRequested)
            {
                PerformJump();
                _jumpRequested = false;
                _jumpBufferTimer = 0f;
            }
        }

        // ─── Rotation ───

        private void UpdateFacingRotation()
        {
            if (!IsMoving) return;

            // Rotate to face movement direction (around gravity axis)
            Quaternion targetRotation = Quaternion.LookRotation(
                _worldMoveDirection, _gravityUp);

            transform.rotation = Quaternion.RotateTowards(
                transform.rotation,
                targetRotation,
                rotationSpeed * Time.fixedDeltaTime);
        }

        // ─── Public API ───

        /// <summary>
        /// Set movement input externally (for mobile virtual joystick).
        /// </summary>
        public void SetMoveInput(Vector2 input)
        {
            _moveInput = new Vector3(input.x, 0f, input.y);
            IsMoving = _moveInput.sqrMagnitude > joystickDeadZone * joystickDeadZone;
        }

        /// <summary>
        /// Trigger a jump externally (for mobile jump button).
        /// </summary>
        public void TriggerJump()
        {
            _jumpRequested = true;
            _jumpBufferTimer = jumpBufferTime;
        }

        // ─── Debug ───

        private void OnDrawGizmosSelected()
        {
            if (_capsule == null) return;

            // Ground check visualization
            Vector3 origin = transform.position + transform.up * (_capsule.radius * 0.9f);
            Gizmos.color = IsGrounded ? Color.green : Color.red;
            Gizmos.DrawWireSphere(
                origin - transform.up * (_capsule.radius + groundCheckDistance),
                groundCheckRadius);

            // Gravity up direction
            Gizmos.color = Color.cyan;
            Gizmos.DrawRay(transform.position, _gravityUp * 2f);
        }
    }
}
